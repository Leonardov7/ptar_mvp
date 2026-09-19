<template>
  <div class="app-layout">
    <header class="top-nav">
      <h1>Sistema Inteligente de Gestión del Conocimiento PTAR</h1>
      <div class="nav-controls">
        <span class="version">v1.0.0</span>
        <!-- BOTÓN DE CONFIGURACIÓN Y GESTIÓN -->
        <button class="btn-config" @click="isConfigOpen = true" title="Configuraciones y Gestión">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>
      </div>
    </header>

    <main class="main-content">
      <aside class="control-panel">
        <Equalizer @update-settings="handleSettingsUpdate" />
        <Dropzone />
        <CaseForm />
      </aside>

      <section class="inference-panel">
        <ChatInterface :equalizerSettings="currentSettings" />
      </section>
    </main>
    <footer class="app-footer">
      developed by Leonardo Valderrama and Gemini version 1.0.0
    </footer>

    <!-- INYECCIÓN DEL MODAL DE CONFIGURACIÓN -->
    <ConfigModal v-if="isConfigOpen" @close="isConfigOpen = false" />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Equalizer from './components/Equalizer.vue';
import Dropzone from './components/Dropzone.vue';
import CaseForm from './components/CaseForm.vue';
import ChatInterface from './components/ChatInterface.vue';
import ConfigModal from './components/ConfigModal.vue';

const isConfigOpen = ref(false);

const currentSettings = ref({
  userProfile: 'operator',
  similarityThreshold: 0.85
});

const handleSettingsUpdate = (newSettings) => {
  currentSettings.value = newSettings;
};
</script>

<style>
*, *::before, *::after {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  height: 100%;
}

#app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-layout {
  display: flex;
  flex-direction: column;
  height: 100%;
  background-color: #ecf0f1;
}

.top-nav {
  background-color: #1a252f;
  color: #ecf0f1;
  padding: 15px 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  z-index: 10;
}

.top-nav h1 {
  margin: 0;
  font-size: 1.4rem;
  letter-spacing: 0.5px;
}

.nav-controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.version {
  font-size: 0.85rem;
  opacity: 0.7;
  font-family: monospace;
}

.btn-config {
  background: none;
  border: none;
  color: #ecf0f1;
  cursor: pointer;
  padding: 5px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0.8;
}

.btn-config:hover {
  transform: rotate(45deg);
  opacity: 1;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  padding: 20px;
  gap: 20px;
}

.control-panel {
  width: 450px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  scrollbar-width: thin;
}

.control-panel::-webkit-scrollbar {
  width: 6px;
}
.control-panel::-webkit-scrollbar-thumb {
  background-color: #bdc3c7;
  border-radius: 4px;
}

.inference-panel {
  flex: 1;
  min-width: 0;
}
.app-footer {
  text-align: right;
  padding: 8px 20px;
  background-color: #ecf0f1;
  color: #7f8c8d;
  font-size: 0.75rem;
  font-family: monospace;
  border-top: 1px solid #bdc3c7;
}
</style>