frontend/
├── src/
│   ├── routes/              # 🎯 Páginas (routing automático)
│   │   ├── +page.svelte     # Página principal (/)
│   │   └── +layout.svelte   # Layout global
│   │
│   ├── lib/                 # 📦 Componentes reutilizables
│   │   └── index.ts
│   │
│   ├── app.css             # 🎨 Estilos globales (Tailwind)
│   └── app.html            # 📄 HTML base
│
├── static/                  # 📁 Archivos estáticos
├── svelte.config.js        # ⚙️ Config de Svelte
└── vite.config.ts          # ⚙️ Config de Vite