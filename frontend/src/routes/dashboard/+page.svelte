<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { fetchAPI, getToken, removeToken } from '$lib/api';

  let documents: any[] = [];
  let loading = true;
  let error = '';

  // Verificar autenticación
  onMount(async () => {
    const token = getToken();
    if (!token) {
      goto('/login');
      return;
    }

    await loadDocuments();
  });

  async function loadDocuments() {
    loading = true;
    error = '';

    try {
      const response = await fetchAPI('/api/documents/');

      if (!response.ok) {
        if (response.status === 401) {
          removeToken();
          goto('/login');
          return;
        }
        throw new Error('Error al cargar documentos');
      }

      documents = await response.json();
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al cargar documentos';
    } finally {
      loading = false;
    }
  }

  function handleLogout() {
    removeToken();
    goto('/login');
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  function getStatusBadge(status: string) {
    const badges = {
      processing: { color: 'bg-yellow-100 text-yellow-800', text: 'Procesando' },
      ready: { color: 'bg-green-100 text-green-800', text: 'Listo' },
      failed: { color: 'bg-red-100 text-red-800', text: 'Error' }
    };
    return badges[status as keyof typeof badges] || badges.processing;
  }
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <header class="bg-white shadow">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
      <h1 class="text-2xl font-bold text-gray-900">
        Sistema RAG de Documentos
      </h1>
      <button
        on:click={handleLogout}
        class="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-md"
      >
        Cerrar Sesión
      </button>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="space-y-8">
      <!-- Upload Section -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">
          Subir Documento
        </h2>
        <p class="text-sm text-gray-600 mb-4">
          Sube un archivo PDF para comenzar a hacer consultas
        </p>
        <button
          class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
          on:click={() => goto('/dashboard/upload')}
        >
          Subir PDF
        </button>
      </div>

      <!-- Documents List -->
      <div class="bg-white shadow rounded-lg p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">
          Mis Documentos
        </h2>

        {#if loading}
          <div class="text-center py-8">
            <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p class="mt-2 text-sm text-gray-600">Cargando documentos...</p>
          </div>
        {:else if error}
          <div class="text-red-600 text-sm bg-red-50 p-4 rounded">
            {error}
          </div>
        {:else if documents.length === 0}
          <div class="text-center py-8 text-gray-500">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p class="mt-2 text-sm">No tienes documentos aún</p>
            <p class="text-sm text-gray-400">Sube tu primer PDF para comenzar</p>
          </div>
        {:else}
          <div class="space-y-3">
            {#each documents as doc}
              <div class="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition">
                <div class="flex items-start justify-between">
                  <div class="flex-1">
                    <h3 class="text-sm font-medium text-gray-900">
                      {doc.original_filename}
                    </h3>
                    <div class="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>{formatDate(doc.created_at)}</span>
                      {#if doc.page_count}
                        <span>{doc.page_count} páginas</span>
                      {/if}
                      {#if doc.chunk_count}
                        <span>{doc.chunk_count} fragmentos</span>
                      {/if}
                    </div>
                  </div>
                  <span class={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(doc.status).color}`}>
                    {getStatusBadge(doc.status).text}
                  </span>
                </div>

                {#if doc.status === 'ready'}
                  <div class="mt-3">
                    
                    <a href={`/dashboard/query?doc=${doc.id}`}
                      class="text-sm text-blue-600 hover:text-blue-800 font-medium"
                    >
                      Hacer consultas →
                    </a>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

<!-- INICIO -->
<!-- FIN -->
    </div>
  </main>
</div>