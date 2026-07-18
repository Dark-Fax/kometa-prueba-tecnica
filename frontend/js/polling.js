const polling = {
    intervalId: null,

    start(taskId, { onComplete, onError, intervalMs = 3000, timeoutMs = 120000 }) {
        this.stop();

        const startTime = Date.now();

        this.intervalId = setInterval(async () => {
            if (Date.now() - startTime > timeoutMs) {
                this.stop();
                onError('La generación tardó demasiado. Intenta de nuevo.');
                return;
            }

            try {
                const data = await api.pollStatus(taskId);

                if (data.status === 'completed') {
                    this.stop();
                    onComplete(data.course_data);
                } else if (data.status === 'error') {
                    this.stop();
                    onError('La IA no pudo generar el curso. Intenta con otra instrucción.');
                }
            } catch (err) {
                this.stop();
                onError('Error de conexión durante la generación.');
            }
        }, intervalMs);
    },

    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
};