import axios from 'axios';

// La URL base asume que el usuario accede al frontend a través de localhost 
// y el backend expone sus puertos en el host.
const API_BASE_URL = 'http://localhost:8000/api/v1';

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
    }
};