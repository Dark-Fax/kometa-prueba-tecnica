const API_BASE = 'http://localhost:8000'; // ajusta al puerto real de tu FastAPI

const api = {
    async generateCourse(instruction) {
        const res = await fetch(`${API_BASE}/courses/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instruction })
        });
        if (!res.ok) throw new Error(`generateCourse failed: ${res.status}`);
        return res.json();
    },

    async pollStatus(taskId) {
        const res = await fetch(`${API_BASE}/courses/status/${taskId}`);
        if (!res.ok) throw new Error(`pollStatus failed: ${res.status}`);
        return res.json();
    },

    async confirmCourse(taskId, courseData) {
        const res = await fetch(`${API_BASE}/courses/confirm/${taskId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ course_data: courseData })
        });
        if (!res.ok) throw new Error(`confirmCourse failed: ${res.status}`);
        return res.json();
    },

    async sendChat(taskId, question, history) {
        const res = await fetch(`${API_BASE}/courses/${taskId}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, history })
        });
        if (!res.ok) throw new Error(`sendChat failed: ${res.status}`);
        return res.json();
    },

    async listCourses() {
        const res = await fetch(`${API_BASE}/courses/list`);
        if (!res.ok) throw new Error(`listCourses failed: ${res.status}`);
        return res.json();
    },

    async deleteCourse(courseDbId) {
        const res = await fetch(`${API_BASE}/courses/${courseDbId}`, {
            method: 'DELETE'
        });
        if (!res.ok) throw new Error(`deleteCourse failed: ${res.status}`);
        return res.json();
    }
};