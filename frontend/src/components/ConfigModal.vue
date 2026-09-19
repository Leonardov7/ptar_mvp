<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content config-modal">
      <div class="modal-header">
        <h2>Configuración del Sistema</h2>
        <button class="btn-close" @click="$emit('close')">&times;</button>
      </div>

      <div class="config-body">
        <!-- VISTA DE MENÚ PRINCIPAL -->
        <div v-if="currentView === 'menu'" class="menu-view">
          <button class="menu-action-btn" @click="openListView">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            Gestión de Bitácora
          </button>
        </div>

        <!-- VISTA DE LISTA COMPACTA -->
        <div v-else-if="currentView === 'list'" class="list-view">
          <div class="view-header">
            <button class="btn-back" @click="currentView = 'menu'">← Volver</button>
            <h3>Mapeo del volumen de conocimientos de operarios</h3>
          </div>
          
          <div v-if="isLoading" class="loading-state">Cargando registros...</div>
          <div v-else-if="error" class="error-state">{{ error }}</div>
          <div v-else-if="cases.length === 0" class="empty-state">No hay casos registrados en el sistema.</div>
          
          <div v-else class="cases-compact-list">
            <div v-for="c in cases" :key="c.id" class="compact-case-item">
              <div class="case-info" @click="openDetailView(c)">
                <span class="c-id">ID: {{ c.id }}</span>
                <span class="c-author">{{ c.author }}</span>
                <span class="c-date" v-if="c.created_at">{{ new Date(c.created_at).toLocaleDateString() }}</span>
              </div>
              <div class="case-quick-actions">
                <button @click.stop="openEditView(c)" class="icon-btn" title="Editar">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                </button>
                <button @click.stop="confirmDelete(c.id)" class="icon-btn" title="Eliminar">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#e74c3c" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- VISTA DE DETALLE O EDICIÓN -->
        <div v-else-if="currentView === 'detail' || currentView === 'edit'" class="detail-view">
          <div class="view-header">
            <button class="btn-back" @click="currentView = 'list'">← Volver a la lista</button>
            <h3 v-if="currentView === 'detail'">Detalle del Registro ID: {{ activeCase.id }}</h3>
            <h3 v-else>Modificando Registro ID: {{ activeCase.id }}</h3>
          </div>

          <!-- MODO DETALLE (SOLO LECTURA) -->
          <div v-if="currentView === 'detail'" class="case-details">
            <div class="detail-row">
              <strong>Autor:</strong> <span>{{ activeCase.author }}</span>
            </div>
            <div class="detail-row">
              <strong>Síntomas:</strong> <span>{{ activeCase.symptoms }}</span>
            </div>
            <div class="detail-row">
              <strong>Acción Ejecutada:</strong> <span>{{ activeCase.action_taken }}</span>
            </div>
            <div class="detail-row">
              <strong>Resultado:</strong> <span>{{ activeCase.result }}</span>
            </div>
          </div>

          <!-- MODO EDICIÓN -->
          <div v-if="currentView === 'edit'" class="case-details edit-form">
            <div class="form-group">
              <label>Autor:</label>
              <input type="text" v-model="editForm.author" :disabled="isActionPending" />
            </div>
            <div class="form-group">
              <label>Síntomas:</label>
              <textarea v-model="editForm.symptoms" rows="3" :disabled="isActionPending"></textarea>
            </div>
            <div class="form-group">
              <label>Acción Ejecutada:</label>
              <textarea v-model="editForm.action_taken" rows="3" :disabled="isActionPending"></textarea>
            </div>
            <div class="form-group">
              <label>Resultado Operativo:</label>
              <textarea v-model="editForm.result" rows="3" :disabled="isActionPending"></textarea>
            </div>
            <div class="form-actions">
              <button class="btn-save" @click="saveEdit" :disabled="isActionPending">
                {{ isActionPending ? 'Guardando...' : 'Guardar Cambios' }}
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import api from '../services/api.js';

defineEmits(['close']);

const currentView = ref('menu'); // 'menu', 'list', 'detail', 'edit'
const cases = ref([]);
const isLoading = ref(false);
const error = ref('');
const isActionPending = ref(false);

const activeCase = ref(null);
const editForm = reactive({
  author: '',
  symptoms: '',
  action_taken: '',
  result: ''
});

const fetchCases = async () => {
  isLoading.value = true;
  error.value = '';
  try {
    const response = await api.getEmpiricalCases();
    cases.value = response.data || [];
  } catch (err) {
    error.value = 'Fallo de red al intentar recuperar los casos almacenados.';
  } finally {
    isLoading.value = false;
  }
};

const openListView = async () => {
  currentView.value = 'list';
  await fetchCases();
};

const openDetailView = (c) => {
  activeCase.value = c;
  currentView.value = 'detail';
};

const openEditView = (c) => {
  activeCase.value = c;
  editForm.author = c.author;
  editForm.symptoms = c.symptoms;
  editForm.action_taken = c.action_taken;
  editForm.result = c.result;
  currentView.value = 'edit';
};

const confirmDelete = async (id) => {
  if (confirm('Esta acción eliminará permanentemente el registro. ¿Desea proceder?')) {
    isActionPending.value = true;
    try {
      await api.deleteEmpiricalCase(id);
      await fetchCases();
    } catch (err) {
      alert('Error al intentar eliminar el caso.');
    } finally {
      isActionPending.value = false;
    }
  }
};

const saveEdit = async () => {
  if (!editForm.author || !editForm.symptoms || !editForm.action_taken || !editForm.result) {
    alert("Todos los campos son obligatorios.");
    return;
  }
  isActionPending.value = true;
  try {
    await api.updateEmpiricalCase(activeCase.value.id, {
      author: editForm.author,
      symptoms: editForm.symptoms,
      action_taken: editForm.action_taken,
      result: editForm.result
    });
    await fetchCases();
    currentView.value = 'list';
  } catch (err) {
    alert('Fallo durante la actualización.');
  } finally {
    isActionPending.value = false;
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 2000;
}

.config-modal {
  background-color: white;
  padding: 30px;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  min-height: 400px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #34495e;
  padding-bottom: 10px;
  margin-bottom: 20px;
}

.modal-header h2 {
  margin: 0;
  color: #2c3e50;
  font-size: 1.4rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.8rem;
  color: #7f8c8d;
  cursor: pointer;
}

.btn-close:hover {
  color: #e74c3c;
}

.config-body {
  overflow-y: auto;
  flex: 1;
}

/* MENU VIEW */
.menu-view {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 15px;
}

.menu-action-btn {
  background-color: #f8f9fa;
  border: 1px solid #d5dbdb;
  border-radius: 8px;
  padding: 20px;
  font-size: 1.1rem;
  color: #2c3e50;
  font-weight: bold;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: all 0.2s;
}

.menu-action-btn:hover {
  background-color: #ebf5fb;
  border-color: #3498db;
  color: #3498db;
}

/* HEADER SECUNDARIO */
.view-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ecf0f1;
}

.view-header h3 {
  margin: 0;
  color: #2980b9;
  font-size: 1.1rem;
}

.btn-back {
  background-color: #ecf0f1;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  cursor: pointer;
  color: #34495e;
  font-weight: bold;
}

.btn-back:hover {
  background-color: #bdc3c7;
}

/* LISTA COMPACTA */
.cases-compact-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.compact-case-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fdfefe;
  border: 1px solid #d5dbdb;
  border-radius: 6px;
  padding: 10px 15px;
  transition: background-color 0.2s;
}

.compact-case-item:hover {
  background-color: #f4f6f7;
}

.case-info {
  display: flex;
  align-items: center;
  gap: 20px;
  flex: 1;
  cursor: pointer;
}

.c-id {
  font-weight: bold;
  color: #8e44ad;
  min-width: 60px;
}

.c-author {
  font-weight: bold;
  color: #2c3e50;
}

.c-date {
  color: #7f8c8d;
  font-size: 0.85rem;
}

.case-quick-actions {
  display: flex;
  gap: 10px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.icon-btn:hover {
  background-color: #e0e6ed;
}

/* DETALLE Y EDICION */
.case-details {
  background-color: #fdfefe;
  border: 1px solid #d5dbdb;
  border-radius: 6px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.detail-row strong {
  color: #2c3e50;
  font-size: 0.9rem;
  text-transform: uppercase;
}

.detail-row span {
  color: #34495e;
  line-height: 1.5;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 0.9rem;
  font-weight: bold;
  color: #2c3e50;
}

.form-group input, .form-group textarea {
  padding: 10px;
  border: 1px solid #bdc3c7;
  border-radius: 4px;
  font-family: inherit;
  font-size: 0.95rem;
}

.form-group input:focus, .form-group textarea:focus {
  outline: none;
  border-color: #3498db;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.btn-save {
  background-color: #2ecc71;
  color: white;
  border: none;
  padding: 10px 20px;
  font-weight: bold;
  border-radius: 4px;
  cursor: pointer;
}

.btn-save:hover:not(:disabled) {
  background-color: #27ae60;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 30px;
  color: #7f8c8d;
}

.error-state {
  color: #e74c3c;
}
</style>