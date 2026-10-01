# Funcionamiento Svelte

¡Perfecto! Te voy a explicar cómo funciona Svelte usando el código del registro como ejemplo. Es **mucho más simple** que React.

---

## 🎯 Anatomía de un Componente Svelte

Un archivo `.svelte` tiene 3 partes opcionales:

```svelte
<script>
  // 1. LÓGICA (JavaScript/TypeScript)
</script>

<style>
  /* 2. ESTILOS (CSS - opcional) */
</style>

<!-- 3. TEMPLATE (HTML) -->
```

---

## 📋 Desglosando el Register

### 1. **Variables Reactivas** (sin useState)

```svelte
<script lang="ts">
  let email = '';           // ← Así de simple
  let password = '';
  let loading = false;
</script>
```

**En React harías:**

```jsx
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [loading, setLoading] = useState(false);
```

**En Svelte:** Solo declaras la variable. Svelte detecta automáticamente cuando cambia.

---

### 2. **Binding de Inputs** (sin onChange)

```svelte
<input
  type="email"
  bind:value={email}
/>
```

**¿Qué hace `bind:value`?**

- **Lectura:** Muestra el valor de `email` en el input
- **Escritura:** Cuando escribes en el input, actualiza `email` automáticamente

**En React harías:**

```jsx
<input
  type="email"
  value={email}
  onChange={(e) => setEmail(e.target.value)}
/>
```

**En Svelte:** `bind:value={email}` = lectura + escritura en una sola línea.

---

### 3. **Manejo de Eventos** (sin preventDefault manual)

```svelte
<form on:submit|preventDefault={handleLogin}>
```

**Desglose:**

- `on:submit` = escucha el evento submit
- `|preventDefault` = llama automáticamente a `e.preventDefault()`
- `{handleLogin}` = función a ejecutar

**En React harías:**

```jsx
<form onSubmit={(e) => {
  e.preventDefault();
  handleLogin();
}}>
```

**En Svelte:** Los modificadores de eventos (como `|preventDefault`) son atajos súper útiles.

---

### 4. **Renderizado Condicional** (sin ternarios)

```svelte
{#if error}
  <div class="text-red-600">
    {error}
  </div>
{/if}
```

**Bloques en Svelte:**

- `{#if condicion}` = Abre el bloque
- `{:else}` = Opcional
- `{/if}` = Cierra el bloque

**En React harías:**

```jsx
{error && (
  <div className="text-red-600">
    {error}
  </div>
)}
```

---

### 5. **Reactividad Automática**

```svelte
<script>
  let loading = false;

  async function handleRegister() {
    loading = true;  // ← UI se actualiza automáticamente
    // ...
    loading = false; // ← UI se actualiza automáticamente
  }
</script>

<button disabled={loading}>
  {loading ? 'Registrando...' : 'Registrarse'}
</button>
```

**¿Qué pasa aquí?**

1. Cambias `loading = true`
2. Svelte detecta el cambio automáticamente
3. El DOM se actualiza (el botón se deshabilita y cambia el texto)

**En React necesitas:**

```jsx
const [loading, setLoading] = useState(false);
setLoading(true); // Solo así React detecta el cambio
```

---

## 🔄 Comparación Completa: React vs Svelte

### **React (Formulario)**

```jsx
function Register() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (!response.ok) throw new Error('Error');
      // ...
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      {error && <div>{error}</div>}
      <button disabled={loading}>
        {loading ? 'Registrando...' : 'Registrarse'}
      </button>
    </form>
  );
}
```

### **Svelte (Mismo Formulario)**

```svelte
<script>
  let email = '';
  let password = '';
  let loading = false;
  let error = '';

  async function handleSubmit() {
    loading = true;
    error = '';
    
    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      
      if (!response.ok) throw new Error('Error');
      // ...
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit}>
  <input type="email" bind:value={email} />
  <input type="password" bind:value={password} />
  {#if error}
    <div>{error}</div>
  {/if}
  <button disabled={loading}>
    {loading ? 'Registrando...' : 'Registrarse'}
  </button>
</form>
```

---

## 🎯 Conceptos Clave de Svelte

### 1. **Reactividad por Compilación**

Svelte compila tu código en JavaScript vanilla optimizado. No usa Virtual DOM como React.

```svelte
let count = 0;  // Svelte detecta que esto puede cambiar
count = 5;      // UI se actualiza automáticamente
```

### 2. **Declaraciones Reactivas** ($:)

```svelte
<script>
  let count = 0;
  $: doubled = count * 2;  // ← Se recalcula cuando count cambia
</script>

<p>{count} * 2 = {doubled}</p>
```

### 3. **Binding Bidireccional**

```svelte
<input bind:value={name} />
```
Es equivalente a:
```svelte
<input
  value={name}
  on:input={(e) => name = e.target.value}
/>
```

### 4. **Modificadores de Eventos**

```svelte
on:click|once           <!-- Solo una vez -->
on:submit|preventDefault <!-- Previene default -->
on:click|stopPropagation <!-- Stop propagation -->
on:click|capture         <!-- Capture phase -->
```

---

## 📚 Más Ejemplos del Register

### **Imports**

```svelte
<script lang="ts">
  import { goto } from '$app/navigation';  // SvelteKit routing
  import { fetchAPI } from '$lib/api';      // Tu helper
</script>
```

### **Función async**

```svelte
<script>
  async function handleRegister() {
    // ... código async normal
  }
</script>
```

### **Interpolación de Variables**

```svelte
{loading ? 'Registrando...' : 'Registrarse'}
```

### **Bloques Condicionales**

```svelte
{#if success}
  <div>¡Éxito!</div>
{:else if error}
  <div>{error}</div>
{:else}
  <form>...</form>
{/if}
```

### **Iteración (no lo usamos aquí, pero útil)**

```svelte
{#each items as item}
  <div>{item.name}</div>
{/each}
```

---

## ✅ Resumen: Por qué Svelte es más simple

| Concepto | React | Svelte |
|----------|-------|--------|
| **Estado** | `useState` | `let variable` |
| **Input binding** | `value + onChange` | `bind:value` |
| **Eventos** | `onClick={fn}` | `on:click={fn}` |
| **Prevent default** | `e.preventDefault()` | `on:click\|preventDefault` |
| **Condicionales** | `{cond && <div>}` | `{#if cond}<div>{/if}` |
| **Loops** | `.map()` | `{#each}` |
| **Efectos** | `useEffect` | `$:` o `onMount` |

---

## 🎓 ¿Algo específico del código que no entiendes?

Puedo explicarte:

- `goto()` - Navegación programática
- `fetchAPI()` - Tu helper personalizado
- `setTimeout(() => goto('/login'), 2000)` - Redirección después de éxito
- Cualquier otra parte

**¿Tiene sentido?** ¿Qué parte quieres que profundice? 🤔
