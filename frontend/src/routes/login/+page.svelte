<script lang="ts">
  import { goto } from '$app/navigation';
  import { fetchAPI, setToken } from '$lib/api';

  let email = '';
  let password = '';
  let error = '';
  let loading = false;

  async function handleLogin() {
    error = '';
    loading = true;

    try {
      const response = await fetchAPI('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al iniciar sesión');
      }

      // Guardar token y redirigir
      setToken(data.access_token);
      goto('/dashboard');
    } catch (err) {
      error = err instanceof Error ? err.message : 'Ocurrió un error';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="max-w-md w-full space-y-8 p-8">
    <div>
      <h2 class="text-center text-3xl font-bold text-gray-900">
        Sistema de Respuestas IA
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Ingresa a tu cuenta
      </p>
    </div>

    <form on:submit|preventDefault={handleLogin} class="mt-8 space-y-6">
      <div class="space-y-4">
        <div>
          <label for="email" class="block text-sm font-medium text-gray-700">
            Correo Electrónico
          </label>
          <input
            id="email"
            type="email"
            bind:value={email}
            required
            disabled={loading}
            placeholder="usuario@ejemplo.com"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">
            Contraseña
          </label>
          <input
            id="password"
            type="password"
            bind:value={password}
            required
            disabled={loading}
            placeholder="••••••••"
            class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {#if error}
        <div class="text-red-600 text-sm bg-red-50 p-3 rounded">
          {error}
        </div>
      {/if}

      <button
        type="submit"
        disabled={loading}
        class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? 'Iniciando sesión...' : 'Iniciar Sesión'}
      </button>

      <p class="text-center text-sm text-gray-600">
        ¿No tienes cuenta?
        <a href="/registro" class="font-medium text-blue-600 hover:text-blue-500">
          Regístrate
        </a>
      </p>
    </form>
  </div>
</div>