import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { visualizer } from 'rollup-plugin-visualizer'

export default defineConfig(({ mode }) => {
  // Załaduj zmienne z .env.{mode}
  const env = loadEnv(mode, process.cwd(), '')

  return {
    plugins: [
      react(),

      // Bundle analyzer - generates stats.html in dist/
      visualizer({
        filename: 'dist/stats.html',
        open: false,
        gzipSize: true,
        brotliSize: true,
      }),
    ],

    define: {
      // Przekaż zmienne do aplikacji
      'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL),
    },

    build: {
      sourcemap: false,
      target: 'es2020',
      chunkSizeWarningLimit: 1000,

      rollupOptions: {
        output: {
          manualChunks: {
            // React core
            'react-vendor': ['react', 'react-dom', 'react-router-dom'],

            // Icons
            'lucide-icons': ['lucide-react'],

            // UI libs
            'ui-vendor': ['react-hot-toast'],

            // Admin (lazy-loaded)
            admin: [
              './src/components/admin/AwardTypesManager.jsx',
              './src/components/admin/UsersManager.jsx',
              './src/components/admin/ClipsManager.jsx',
              './src/components/admin/StatsPanel.jsx',
            ],

            // Mobile (lazy-loaded)
            mobile: [
              './src/components/mobile/VerticalFeed.jsx',
              './src/components/mobile/VerticalVideoPlayer.jsx',
              './src/components/mobile/AwardButton.jsx',
            ],
          },

          chunkFileNames: 'assets/[name]-[hash].js',
          entryFileNames: 'assets/[name]-[hash].js',
          assetFileNames: 'assets/[name]-[hash].[ext]',
        },
      },

      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: mode === 'production',
          drop_debugger: true,
          pure_funcs: ['console.log', 'console.debug'],
        },
      },
    },

    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        'axios',
        'lucide-react',
      ],
    },

    server: {
      port: 5173,
      strictPort: false,
      open: false,
      cors: true,
    },

    preview: {
      port: 4173,
      strictPort: false,
    },
  }
})
