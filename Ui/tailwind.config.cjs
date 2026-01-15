/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#2563eb',
                secondary: '#64748b',
                accent: '#f59e0b',
                success: '#10b981',
                danger: '#ef4444',
            },
        },
    },
    plugins: [],
}