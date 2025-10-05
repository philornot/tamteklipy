import {defineConfig, loadEnv} from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({mode}) => {
    // Załaduj zmienne z .env.{mode}
    const env = loadEnv(mode, process.cwd(), '')

    return {
        plugins: [react()],
        define: {
            // Przekaż zmienne do aplikacji
            'import.meta.env.VITE_API_URL': JSON.stringify(env.VITE_API_URL)
        }
    }
})