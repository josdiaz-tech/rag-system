<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { browser } from '$app/environment';
  import { fetchAPI, getToken, removeToken } from '$lib/api';
  import { marked } from 'marked';

  let question = '';
  let loading = false;
  let error = '';
  let queryHistory: any[] = [];
  let selectedDocId = '';

  // Configurar marked para mejor renderizado
  marked.setOptions({
    breaks: true, // Convertir saltos de línea en <br>
    gfm: true, // GitHub Flavored Markdown
  });

  // Verificar autenticación y obtener doc_id de URL
  onMount(async () => {
    const token = getToken();
    if (!token) {
      goto('/login');
      return;
    }

    // Obtener doc_id de query params - solo en el cliente
    if (browser) {
      const urlParams = new URLSearchParams(window.location.search);
      selectedDocId = urlParams.get('doc') || '';
    }

    // Cargar historial
    await loadHistory();
  });

  async function loadHistory() {
    try {
      const response = await fetchAPI('/api/query/history?limit=10');

      if (!response.ok) {
        if (response.status === 401) {
          removeToken();
          goto('/login');
          return;
        }
        throw new Error('Error al cargar historial');
      }

      queryHistory = await response.json();
    } catch (err) {
      console.error('Error loading history:', err);
    }
  }

  async function handleSubmit() {
    if (!question.trim()) {
      error = 'Por favor escribe una pregunta';
      return;
    }

    loading = true;
    error = '';

    try {
      const body: any = { question };
      
      // Si hay un documento seleccionado, incluirlo
      if (selectedDocId) {
        body.document_ids = [selectedDocId];
      }

      const response = await fetchAPI('/api/query/', {
        method: 'POST',
        body: JSON.stringify(body)
      });

      const data = await response.json();

      if (!response.ok) {
        if (response.status === 401) {
          removeToken();
          goto('/login');
          return;
        }
        throw new Error(data.detail || 'Error al procesar la consulta');
      }

      // Agregar la nueva consulta al historial
      queryHistory = [data, ...queryHistory];
      
      // Limpiar el input
      question = '';
    } catch (err) {
      error = err instanceof Error ? err.message : 'Error al procesar la consulta';
    } finally {
      loading = false;
    }
  }

  function formatDate(dateString: string): string {
    if (!browser) return '';
    
    return new Date(dateString).toLocaleDateString('es-ES', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  // Función para convertir markdown a HTML
  function renderMarkdown(text: string): string {
    if (!browser || !text) return '';
    return marked(text);
  }
</script>

<div class="min-h-screen bg-gray-50">
  <!-- Header -->
  <header class="bg-white shadow">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center">
          <button
            aria-label="ir al dashboard"
            on:click={() => goto('/dashboard')}
            class="mr-4 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
          </button>
          <h1 class="text-2xl font-bold text-gray-900">
            Consultas de Documentos
          </h1>
        </div>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="space-y-6">
      <!-- Query Input Card -->
      <div class="bg-white shadow-sm rounded-lg border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-4">
            Nueva Consulta
          </h2>
          
          <form on:submit|preventDefault={handleSubmit} class="space-y-4">
            <div>
              <label for="question" class="block text-sm font-medium text-gray-700 mb-2">
                Escribe tu pregunta
              </label>
              <textarea
                id="question"
                bind:value={question}
                disabled={loading}
                rows="4"
                placeholder="Por ejemplo: ¿Cómo instalar fibra óptica FTTH? ¿Cuáles son los pasos de instalación?"
                class="block w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none transition-shadow"
              />
            </div>

            {#if error}
              <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg text-sm">
                <div class="flex items-center">
                  <svg class="h-5 w-5 mr-2 shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                  {error}
                </div>
              </div>
            {/if}

            <button
              type="submit"
              disabled={loading || !question.trim()}
              class="w-full flex justify-center items-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {#if loading}
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white shrink-0" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                Procesando consulta...
              {:else}
                <svg class="h-5 w-5 mr-2 inline-block shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Enviar Pregunta
              {/if}
            </button>
          </form>
        </div>
      </div>

      <!-- Query History -->
      <div class="bg-white shadow-sm rounded-lg border border-gray-200">
        <div class="p-6">
          <h2 class="text-lg font-semibold text-gray-900 mb-6">
            Historial de Consultas (ultimas 10)
          </h2>

          {#if queryHistory.length === 0}
            <div class="text-center py-12">
              <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p class="mt-4 text-base text-gray-600 font-medium">No hay consultas aún</p>
              <p class="mt-1 text-sm text-gray-500">Haz tu primera pregunta arriba para comenzar</p>
            </div>
          {:else}
            <div class="space-y-6">
              {#each queryHistory as query, index (query.id)}
                <div class="border border-gray-200 rounded-lg overflow-hidden hover:border-gray-300 transition-colors">
                  <!-- Question Section -->
                  <div class="bg-blue-50 px-5 py-4 border-b border-blue-100">
                    <div class="flex items-start space-x-3">
                      <div class="shrink-0 mt-1">
                        <div class="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                          <svg class="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                      </div>
                      <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-gray-900 leading-relaxed">
                          {query.question}
                        </p>
                        <p class="mt-1 text-xs text-gray-600">
                          {formatDate(query.created_at)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <!-- Answer Section -->
                  <div class="bg-white px-5 py-4">
                    <div class="flex items-start space-x-3">
                      <div class="shrink-0 mt-1">
                        <div class="h-8 w-8 rounded-full bg-green-100 flex items-center justify-center">
                          <svg class="h-5 w-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                        </div>
                      </div>
                      <div class="flex-1 min-w-0">
                        <!-- Renderizar respuesta como Markdown con estilos -->
                        <div class="prose prose-sm max-w-none text-gray-800">
                          {@html renderMarkdown(query.answer)}
                        </div>

                        <!-- Sources Section -->
                        {#if query.sources && query.sources.length > 0}
                          <div class="mt-4 pt-4 border-t border-gray-100">
                            <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
                              Fuentes de Información
                            </p>
                            <div class="space-y-2">
                              {#each query.sources as source, sourceIndex}
                                <div class="flex items-start space-x-2 text-xs">
                                  <span class="inline-flex items-center justify-center h-5 w-5 rounded-full bg-gray-200 text-gray-700 font-medium shrink-0">
                                    {sourceIndex + 1}
                                  </span>
                                  <div class="flex-1 min-w-0">
                                    <span class="font-medium text-gray-900">{source.source_file}</span>
                                    {#if source.chunk_index !== undefined}
                                      <span class="text-gray-500"> • Fragmento {source.chunk_index + 1}</span>
                                    {/if}
                                  </div>
                                </div>
                              {/each}
                            </div>
                          </div>
                        {/if}

                        <!-- Metadata Section -->
                        <div class="mt-4 pt-3 border-t border-gray-100 flex items-center space-x-4 text-xs text-gray-500">
                          {#if query.chunks_retrieved}
                            <span class="flex items-center">
                              <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                              </svg>
                              {query.chunks_retrieved} fragmentos
                            </span>
                          {/if}
                          {#if query.response_time}
                            <span class="flex items-center">
                              <svg class="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {query.response_time.toFixed(2)}s
                            </span>
                          {/if}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </main>
</div>

<style>
  /* Estilos personalizados para el contenido Markdown */
  :global(.prose) {
    color: #1f2937;
  }

  :global(.prose p) {
    margin-bottom: 0.75rem;
    line-height: 1.625;
  }

  :global(.prose strong) {
    color: #111827;
    font-weight: 600;
  }

  :global(.prose em) {
    font-style: italic;
  }

  :global(.prose h1, .prose h2, .prose h3, .prose h4) {
    color: #111827;
    font-weight: 700;
    margin-top: 1.25rem;
    margin-bottom: 0.75rem;
    line-height: 1.25;
  }

  :global(.prose h1) {
    font-size: 1.25rem;
  }

  :global(.prose h2) {
    font-size: 1.125rem;
  }

  :global(.prose h3) {
    font-size: 1rem;
  }

  :global(.prose ul, .prose ol) {
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
    padding-left: 1.5rem;
  }

  :global(.prose ul) {
    list-style-type: disc;
  }

  :global(.prose ol) {
    list-style-type: decimal;
  }

  :global(.prose li) {
    margin-top: 0.25rem;
    margin-bottom: 0.25rem;
  }

  :global(.prose code) {
    background-color: #f3f4f6;
    padding: 0.125rem 0.375rem;
    border-radius: 0.25rem;
    font-size: 0.875em;
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
    color: #dc2626;
  }

  :global(.prose pre) {
    background-color: #1f2937;
    color: #f9fafb;
    padding: 1rem;
    border-radius: 0.5rem;
    overflow-x: auto;
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
  }

  :global(.prose pre code) {
    background-color: transparent;
    padding: 0;
    color: inherit;
    font-size: 0.875rem;
  }

  :global(.prose blockquote) {
    border-left: 4px solid #3b82f6;
    padding-left: 1rem;
    margin-left: 0;
    font-style: italic;
    color: #4b5563;
  }

  :global(.prose a) {
    color: #3b82f6;
    text-decoration: underline;
  }

  :global(.prose a:hover) {
    color: #2563eb;
  }

  :global(.prose hr) {
    border-top: 1px solid #e5e7eb;
    margin-top: 1.5rem;
    margin-bottom: 1.5rem;
  }

  :global(.prose table) {
    width: 100%;
    border-collapse: collapse;
    margin-top: 0.75rem;
    margin-bottom: 0.75rem;
  }

  :global(.prose th, .prose td) {
    border: 1px solid #e5e7eb;
    padding: 0.5rem;
    text-align: left;
  }

  :global(.prose th) {
    background-color: #f9fafb;
    font-weight: 600;
  }
</style>