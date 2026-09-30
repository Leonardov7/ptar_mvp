import axios from 'axios';

const API_BASE_URL = 'http://localhost:8055/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    async submitEmpiricalCase(caseData) {
        try {
            const response = await apiClient.post('/empirical-case', caseData);
            return response.data;
        } catch (error) {
            console.error('Error al enviar el caso empírico:', error);
            throw error;
        }
    },

    /**
     * Sube múltiples manuales técnicos o el contenido de una carpeta.
     * @param {Array<File>} files - Arreglo de archivos PDF.
     */
    async uploadManual(files) {
        try {
            const formData = new FormData();
            files.forEach(file => {
                formData.append('files', file);
            });
            
            const response = await apiClient.post('/upload-manual', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        } catch (error) {
            console.error('Error al subir los manuales técnicos:', error);
            throw error;
        }
    },

    async getEmpiricalCases() {
        try {
            const response = await apiClient.get('/empirical-cases');
            return response.data;
        } catch (error) {
            console.error('Error al obtener los casos empíricos:', error);
            throw error;
        }
    },

    async updateEmpiricalCase(id, caseData) {
        try {
            const response = await apiClient.put(`/empirical-cases/${id}`, caseData);
            return response.data;
        } catch (error) {
            console.error(`Error al actualizar el caso ${id}:`, error);
            throw error;
        }
    },

    async deleteEmpiricalCase(id) {
        try {
            const response = await apiClient.delete(`/empirical-cases/${id}`);
            return response.data;
        } catch (error) {
            console.error(`Error al eliminar el caso ${id}:`, error);
            throw error;
        }
    }
};