<template>
  <div class="text-gray-800 p-6">
    <div class="max-w-7xl mx-auto">
      <h2
        class="text-3xl font-bold mb-6 text-center tracking-wide border-b border-gray-300 pb-6"
      >
        Log Viewer
      </h2>

      <div class="my-6">
        <label for="course" class="mr-2 font-semibold">Select Course:</label>
        <select
          id="course"
          v-model="selectedCourse"
          @change="fetchLogList"
          class="p-2 border border-gray-400 rounded bg-gray-100 focus:outline-none focus:ring-2 focus:ring-green-500"
        >
          <option disabled value="">Please select a course</option>
          <option v-for="course in courses" :key="course.id" :value="course.id">
            {{ course.id }}
          </option>
        </select>
      </div>

      <div v-if="logList.length">
        <ul id="logList" class="list-none p-0">
          <li
            v-for="log in logList"
            :key="log"
            @click="loadLog(log)"
            :class="[
              'my-2 p-2 border-l-4 rounded cursor-pointer transition-colors duration-200 bg-gray-100',
              log === selectedLogFile
                ? 'hover:bg-gray-200 border-cyan-700'
                : 'hover:bg-gray-200 border-transparent',
            ]"
          >
            {{ log }}
          </li>
        </ul>
      </div>

      <div v-if="fileContent" class="mt-6 bg-gray-100 p-4 rounded shadow-lg">
        <div
          v-if="isHTML"
          class="border border-gray-300 p-4 bg-white rounded overflow-x-auto restore-padding"
          v-html="fileContent"
        ></div>
        <pre
          v-else
          class="border border-gray-300 p-4 bg-white rounded overflow-x-auto whitespace-pre-wrap text-sm"
          >{{ fileContent }}
        </pre>
      </div>

      <div v-if="error" class="mt-4 text-red-500">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { computed, ref, watch } from "vue";
import { authStore } from "../store/auth";

export default {
  name: "LogViewer",
  setup() {
    const apiBase = import.meta.env.VITE_API_BASE_URL;
    const courses = ref([]);
    const selectedCourse = ref("");
    const logList = ref([]);
    const fileContent = ref("");
    const error = ref("");
    const selectedLogFile = ref("");

    const studentId = computed(() => {
      if (!authStore.token) return "";
      try {
        const payload = JSON.parse(atob(authStore.token.split(".")[1]));
        return payload.sub;
      } catch (e) {
        return "";
      }
    });

    const isHTML = computed(() => {
      return selectedLogFile.value.toLowerCase().endsWith(".html");
    });

    watch(selectedCourse, () => {
      fileContent.value = "";
      selectedLogFile.value = "";
    });

    const fetchCourses = async () => {
      try {
        const response = await axios.get(`${apiBase}/courses`, {
          headers: {
            Authorization: `Bearer ${authStore.token}`,
          },
        });
        courses.value = response.data;
      } catch (error) {
        console.error("Failed to fetch courses", error);
      }
    };

    const fetchLogList = async () => {
      if (!selectedCourse.value) {
        error.value = "Please select a course.";
        return;
      }
      error.value = "";
      try {
        const response = await axios.get(
          `${apiBase}/courses/${selectedCourse.value}/logs`,
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
            },
          }
        );
        if (response.data && response.data.length === 0) {
          error.value = `No logs found for student id: ${studentId.value}`;
          logList.value = [];
        } else {
          logList.value = response.data;
        }
      } catch (err) {
        console.error(err);
        error.value =
          (err.response && err.response.data.detail) ||
          "Failed to fetch log list.";
      }
    };

    const loadLog = async (logFile) => {
      if (selectedLogFile.value === logFile) {
        selectedLogFile.value = "";
        fileContent.value = "";
        return;
      }
      selectedLogFile.value = logFile;

      try {
        const response = await axios.get(
          `${apiBase}/courses/${selectedCourse.value}/logs/${logFile}`,
          {
            headers: {
              Authorization: `Bearer ${authStore.token}`,
            },
          }
        );
        fileContent.value = response.data.content;
      } catch (err) {
        console.error(err);
        error.value =
          (err.response && err.response.data.detail) ||
          "Failed to fetch log content.";
      }
    };

    fetchCourses();

    return {
      courses,
      selectedCourse,
      logList,
      fileContent,
      error,
      selectedLogFile,
      studentId,
      isHTML,
      fetchLogList,
      loadLog,
    };
  },
};
</script>

<style scoped>
.restore-padding * {
  padding: revert;
  list-style: disc;
}
</style>
