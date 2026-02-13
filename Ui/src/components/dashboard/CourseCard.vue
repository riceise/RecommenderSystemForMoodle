<script setup>
defineProps({
  course: Object 
});
</script>

<template>
  <div class="glass-card hover-lift">
    <div class="flex justify-between items-start mb-4">
      <span class="badge" :class="course.platform.toLowerCase()">
        {{ course.platform }}
      </span>
      <span class="text-xs text-gray-500 font-mono">ID: {{ course.externalId }}</span>
    </div>

    <h3 class="text-xl font-bold text-white mb-2">{{ course.title }}</h3>
    <p class="text-sm text-gray-200 mb-4 opacity-80">{{ course.description }}</p>

    <div class="ai-insight-box">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-xl">🤖</span>
        <span class="font-bold text-yellow-300 text-sm">AI Рекомендация</span>
      </div>
      <p class="text-sm text-white italic">
        "{{ course.aiReason || 'Этот курс поможет закрыть пробелы по результатам последних тестов.' }}"
      </p>
    </div>

    <a :href="course.url" target="_blank" class="btn-action mt-4 block text-center">
      Перейти к курсу
    </a>
  </div>
</template>

<style scoped>
.glass-card {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 24px;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
}

.hover-lift:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.5);
}

.ai-insight-box {
  background: rgba(124, 58, 237, 0.3); 
  border-left: 4px solid #FCD34D; 
  padding: 12px;
  border-radius: 8px;
}

.btn-action {
  background: linear-gradient(90deg, #4f46e5, #9333ea);
  color: white;
  padding: 10px;
  border-radius: 12px;
  font-weight: 600;
  text-decoration: none;
}
</style>