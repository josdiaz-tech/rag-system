<script lang="ts">
  import { goto } from '$app/navigation';
  import { fetchAPI } from '$lib/api';

  let email = '';
  let password = '';
  let fullName = '';
  let error = '';
  let loading = false;
  let success = false;

  async function handleRegister() {
    error = '';
    loading = true;

    try {
      const response = await fetchAPI('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ 
          email, 
          password,
          full_name: fullName 
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al registrarse');
      }

      success = true;
      
      // Redirigir al login después de 2 segundos
      setTimeout(() => {
        goto('/login');
      }, 2000);
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
        Crear Cuenta
      </h2>
      <p class="mt-2 text-center text-sm text-gray-600">
        Regístrate para comenzar a usar el sistema
      </p>
    </div>

    {#if success}
      <div class="bg-green-50 border border-green-200 text-green-700 p-4 rounded">
        ¡Cuenta creada exitosamente! Redirigiendo al inicio de sesión...
      </div>
    {:else}
      <form on:submit|preventDefault={handleRegister} class="mt-8 space-y-6">
        <div class="space-y-4">
          <div>
            <label for="fullName" class="block text-sm font-medium text-gray-700">
              Nombre Completo
            </label>
            <input
              id="fullName"
              type="text"
              bind:value={fullName}
              disabled={loading}
              placeholder="Juan Pérez"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

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
              placeholder="Mínimo 12 caracteres"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p class="mt-1 text-xs text-gray-500">
              Mínimo 12 caracteres, debe incluir mayúscula, número y carácter especial
            </p>
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
          {loading ? 'Registrando...' : 'Registrarse'}
        </button>

        <p class="text-center text-sm text-gray-600">
          ¿Ya tienes cuenta?
          <a href="/login" class="font-medium text-blue-600 hover:text-blue-500">
            Inicia Sesión
          </a>
        </p>
      </form>
    {/if}
  </div>
</div>