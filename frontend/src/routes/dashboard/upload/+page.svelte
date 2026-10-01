<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getToken, removeToken } from '$lib/api';

  let file: File | null = null;
  let uploading = false;
  let error = '';
  let success = false;
  let dragActive = false;

  // Verificar autenticación
  onMount(() => {
    const token = getToken();
    if (!token) {
      goto('/login');
    }
  });

  function handleFileSelect(event: Event) {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files[0]) {
      const selectedFile = target.files[0];
      
      // Validar que sea PDF
      if (selectedFile.type !== 'application/pdf') {
        error = 'Solo se permiten archivos PDF';
        return;
      }

      // Validar tamaño (50MB máximo)
      if (selectedFile.size > 50 * 1024 * 1024) {
        error = 'El archivo no debe superar 50MB';
        return;
      }

      file = selectedFile;
      error = '';
    }
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault();
    dragActive = true;
  }

  function handleDragLeave(event: DragEvent) {
    event.preventDefault();
    dragActive = false;
  }

  function handleDrop(event: DragEvent) {
    event.preventDefault();
    dragActive = false;

    if (event.dataTransfer?.files && event.dataTransfer.files[0]) {
      const droppedFile = event.dataTransfer.files[0];

      // Validar que sea PDF
      if (droppedFile.type !== 'application/pdf') {
        error = 'Solo se permiten archivos PDF';
        return;
      }

      // Validar tamaño (50MB máximo)
      if (droppedFile.size > 50 * 1024 * 1024) {
        error = 'El archivo no debe superar 50MB';
        return;
      }

      file = droppedFile;
      error = '';
    }
  }

  async function handleUpload() {
    if (!file) {
      error = 'Por favor selecciona un archivo';
      return;
    }

    uploading = true;
    error = '';

    try {
      const token = getToken();
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/api/documents/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          removeToken();
          goto('/login');
          return;
        }
        throw new Error(data.detail || 'Error al subir el archivo');
      }

      success = true;
      
      // Redirigir al dashboard después de 2 segundos
      setTimeout(() => {
        goto('/dashboard');
      }, 2000);
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al subir el archivo';
    } finally {
      uploading = false;
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <header class="bg-white shadow">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex items-center">
        <button
          on:click={() => goto('/dashboard')}
          class="mr-4 text-gray-600 hover:text-gray-900"
        >
          ← Volver
        </button>
        <h1 class="text-2xl font-bold text-gray-900">
          Subir Documento PDF
        </h1>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {#if success}
      <div class="bg-green-50 border border-green-200 text-green-700 p-4 rounded-lg">
        <h3 class="font-semibold">¡Documento subido exitosamente!</h3>
        <p class="text-sm mt-1">El documento se está procesando. Redirigiendo al dashboard...</p>
      </div>
    {:else}
      <div class="bg-white shadow rounded-lg p-6">
        <!-- Drag & Drop Area -->
        <div
          role="region" aria-label="Zona de arrastre de archivos"
          class="border-2 border-dashed rounded-lg p-12 text-center transition-colors {dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'}"
          on:dragover={handleDragOver}
          on:dragleave={handleDragLeave}
          on:drop={handleDrop}
        >
          {#if file}
            <div class="space-y-4">
              <svg class="mx-auto h-12 w-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p class="text-sm font-medium text-gray-900">{file.name}</p>
                <p class="text-xs text-gray-500">{formatFileSize(file.size)}</p>
              </div>
              <button
                type="button"
                on:click={() => { file = null; error = ''; }}
                class="text-sm text-red-600 hover:text-red-800"
              >
                Eliminar
              </button>
            </div>
          {:else}
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p class="mt-4 text-sm text-gray-600">
              Arrastra y suelta un archivo PDF aquí, o
            </p>
            <label class="mt-2 cursor-pointer">
              <span class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700">
                Seleccionar archivo
              </span>
              <input
                type="file"
                accept=".pdf,application/pdf"
                class="hidden"
                on:change={handleFileSelect}
                disabled={uploading}
              />
            </label>
            <p class="mt-4 text-xs text-gray-500">
              PDF hasta 50MB
            </p>
          {/if}
        </div>

        {#if error}
          <div class="mt-4 text-red-600 text-sm bg-red-50 p-3 rounded">
            {error}
          </div>
        {/if}

        {#if file}
          <div class="mt-6">
            <button
              type="button"
              on:click={handleUpload}
              disabled={uploading}
              class="w-full flex justify-center py-3 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {#if uploading}
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Subiendo documento...
              {:else}
                Subir Documento
              {/if}
            </button>
          </div>
        {/if}

        <!-- Info Box -->
        <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h3 class="text-sm font-medium text-blue-900 mb-2">
            Información del procesamiento
          </h3>
          <ul class="text-xs text-blue-700 space-y-1">
            <li>• El documento será procesado automáticamente</li>
            <li>• Se extraerá texto e imágenes para análisis</li>
            <li>• Podrás hacer consultas una vez termine el procesamiento</li>
            <li>• El tiempo de procesamiento depende del tamaño del archivo</li>
          </ul>
        </div>
      </div>
    {/if}
  </main>
</div>
