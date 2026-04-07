<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex">
    <aside class="w-64 bg-gray-800 border-r border-gray-700 p-6">
      <h2 class="text-xl font-bold mb-8">Admin Panel</h2>
      <nav class="space-y-4">
        <div class="text-teal-400 font-medium">📊 Дашборд</div>
        <div class="text-gray-400 hover:text-white cursor-pointer">👥 Пользователи</div>
        <div class="text-gray-400 hover:text-white cursor-pointer">📚 Курсы</div>
      </nav>

      <button @click="router.push('/dashboard')" class="mt-10 text-sm text-gray-500 hover:text-white">
        ← Вернуться на сайт
      </button>
    </aside>

    <main class="flex-1 p-10">
      <h1 class="text-3xl font-bold mb-6">Управление системой</h1>
      <div class="bg-gray-800 p-6 rounded-lg border border-gray-700">
        <p>Здесь будет функционал администратора.</p>
      </div>
    </main>
  </div>
</template>