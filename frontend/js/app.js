function kometaApp() {
    return {
        stage: "idle",
        stepIndex: 0,
        taskId: null,
        instruction: "",
        courseData: null,
        moodleCourseId: null,
        chatMessages: [],
        errorMessage: "",
        isEditing: false,
        recentCourses: [],

        init() {
            this.loadRecentCourses();
            this.goTo("idle");
        },

        async loadRecentCourses() {
            try {
                this.recentCourses = await api.listCourses();
            } catch (err) {
                this.recentCourses = [];
            }
        },

        async deleteRecentCourse(courseDbId) {
            if (!confirm('¿Eliminar este curso de Moodle y del historial? Esta acción no se puede deshacer.')) return;
            try {
                await api.deleteCourse(courseDbId);
                this.recentCourses = this.recentCourses.filter(c => c.id !== courseDbId);
            } catch (err) {
                this.errorMessage = 'No se pudo eliminar el curso.';
            }
        },

        async loadScreen(name, targetId = "screens-container") {
            const res = await fetch(`partials/${name}.html`);
            const html = await res.text();
            document.getElementById(targetId).innerHTML = html;
        },

        async goTo(stage) {
            this.stage = stage;
            const map = {
                idle: 0,
                loading: 1,
                preview: 2,
                publishing: 2,
                success: 3,
            };
            this.stepIndex = map[stage] ?? 0;

            const screenMap = {
                idle: "screen-1-instruccion",
                loading: "screen-2-loading",
                preview: "screen-3-preview",
                publishing: "screen-4-publishing",
                success: "screen-5-success",
            };

            await this.loadScreen(screenMap[stage]);

            if (stage === "success") {
                await this.loadScreen("screen-6-chat", "chat-container");
            }
        },

        reset() {
            this.taskId = null;
            this.instruction = "";
            this.courseData = null;
            this.moodleCourseId = null;
            this.chatMessages = [];
            this.errorMessage = "";
            this.goTo("idle");
        },

        async submitInstruction() {
            if (!this.instruction.trim()) return;
            this.errorMessage = "";
            try {
                const { task_id } = await api.generateCourse(this.instruction);
                this.taskId = task_id;
                this.goTo("loading");
                polling.start(task_id, {
                    onComplete: (data) => {
                        this.courseData = data;
                        this.goTo("preview");
                    },
                    onError: (msg) => {
                        this.errorMessage = msg;
                        this.goTo("idle");
                    },
                });
            } catch (err) {
                this.errorMessage =
                    "No se pudo iniciar la generación. Intenta de nuevo.";
            }
        },

        async confirmPublish() {
            this.errorMessage = '';
            this.isEditing = false;
            this.goTo('publishing');
            try {
                const { moodle_course_id } = await api.confirmCourse(this.taskId, this.courseData);
                this.moodleCourseId = moodle_course_id;
                this.loadRecentCourses();
                this.goTo('success');
            } catch (err) {
                this.errorMessage = 'Falló la publicación en Moodle. Puedes reintentar.';
                this.goTo('preview');
            }
        },

        editInstruction() {
            this.goTo("idle");
        },

        toggleEditMode() {
            this.isEditing = !this.isEditing;
        },

        async sendChatMessage(question) {
            if (!question.trim()) return;
            try {
                const { answer } = await api.sendChat(this.taskId, question, this.chatMessages);
                this.chatMessages.push({ question, answer });
            } catch (err) {
                this.chatMessages.push({
                    question,
                    answer: "Error al consultar. Intenta de nuevo.",
                });
            }
        },
    };
}
