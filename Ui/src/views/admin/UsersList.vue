<template>
  <div class="bg-white p-6 rounded-lg shadow-sm">
    <h2 class="text-2xl font-bold mb-6 text-gray-800">Пользователи системы</h2>

    <table class="w-full text-left border-collapse">
      <thead>
      <tr class="text-gray-500 border-b border-gray-200">
        <th class="py-3">Email</th>
        <th class="py-3">ФИО</th>
        <th class="py-3">Moodle Статус</th>
      </tr>
      </thead>
      <tbody>
      <tr v-for="user in users" :key="user.id" class="border-b border-gray-100 hover:bg-gray-50">
        <td class="py-3 font-medium text-gray-700">{{ user.email }}</td>
        <td class="py-3 text-gray-600">{{ user.fullName }}</td>
        <td class="py-3">
          <span v-if="user.moodleUserId > 0" class="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-bold">
              Linked (ID: {{ user.moodleUserId }})
            </span>
          <span v-else class="px-2 py-1 bg-gray-100 text-gray-500 rounded-full text-xs">
              Not Linked
            </span>
        </td>
      </tr>
      </tbody>
    </table>
  </div>
</template>