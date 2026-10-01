<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { getToken } from '$lib/api';

  onMount(() => {
    const token = getToken();
    if (token) {
      goto('/dashboard');
    } else {
      goto('/login');
    }
  });
</script>

<div class="min-h-screen flex items-center justify-center bg-gray-50">
  <div class="text-center">
    <div class="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    <p class="mt-4 text-gray-600">Cargando...</p>
  </div>
</div>
