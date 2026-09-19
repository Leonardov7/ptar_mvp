import axios from 'axios';

// URL base del backend orquestador (Puerto aislado de desarrollo 8055)
const API_BASE_URL = 'http://localhost:8055/api/v1';

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export default {
    /**
     * Envía el reporte empírico a la base de datos vectorial (CBR).
     * @param {Object} caseData - Objeto con symptoms, action_taken, result, author.
     */
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
     * Sube un manual técnico en formato PDF para ser procesado por IBM Docling.
     * @param {File} file - Archivo PDF.
     */
    async uploadManual(file) {
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const response = await apiClient.post('/upload-manual', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            });
            return response.data;
        } catch (error) {
            console.error('Error al subir el manual técnico:', error);
            throw error;
        }
    },

    /**
     * Obtiene el listado de todos los casos empíricos indexados en la base de datos.
     */
    async getEmpiricalCases() {
        try {
            const response = await apiClient.get('/empirical-cases');
            return response.data;
        } catch (error) {
            console.error('Error al obtener los casos empíricos:', error);
            throw error;
        }
    },

    /**
     * Actualiza y re-vectoriza un caso empírico existente.
     * @param {Number} id - Identificador del caso en PostgreSQL.
     * @param {Object} caseData - Datos modificados.
     */
    async updateEmpiricalCase(id, caseData) {
        try {
            const response = await apiClient.put(`/empirical-cases/${id}`, caseData);
            return response.data;
        } catch (error) {
            console.error(`Error al actualizar el caso ${id}:`, error);
            throw error;
        }
    },

    /**
     * Elimina un caso de la base de datos vectorial de manera irreversible.
     * @param {Number} id - Identificador del caso.
     */
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