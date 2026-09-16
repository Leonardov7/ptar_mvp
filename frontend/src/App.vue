<template>
  <div class="app-layout">
    <header class="top-nav">
      <h1>Sistema Inteligente de Gestión del Conocimiento PTAR</h1>
      <span class="version">Arquitectura Híbrida CBR/RAG v1.0</span>
    </header>

    <main class="main-content">
      <!-- Columna Izquierda: Panel de Control y Captura de Datos -->
      <aside class="control-panel">
        <Equalizer @update-settings="handleSettingsUpdate" />
        <Dropzone />
        <CaseForm />
      </aside>

      <!-- Columna Derecha: Interfaz de Interacción Continua -->
      <section class="inference-panel">
        <ChatInterface :equalizerSettings="currentSettings" />
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import Equalizer from './components/Equalizer.vue';
import Dropzone from './components/Dropzone.vue';
import CaseForm from './components/CaseForm.vue';
import ChatInterface from './components/ChatInterface.vue';

// Estado global para las configuraciones del ecualizador
const currentSettings = ref({
  userProfile: 'operator',
  similarityThreshold: 0.85
});

// Receptor del evento emitido por Equalizer.vue
const handleSettingsUpdate = (newSettings) => {
  currentSettings.value = newSettings;
};
</script>

<style>
/* Estilos globales y reset aplicados al contenedor principal */
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

.version {
  font-size: 0.85rem;
  opacity: 0.7;
  font-family: monospace;
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
  /* Ocultar barra de desplazamiento para estética limpia */
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
</style>