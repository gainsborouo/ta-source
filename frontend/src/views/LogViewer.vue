<template>
  <div class="text-gray-800 p-6">
    <div class="max-w-7xl mx-auto">
      <h2
        class="text-3xl font-bold mb-6 text-center tracking-wide border-b border-gray-300 pb-6"
      >
        Log Viewer
      </h2>

      <div class="flex items-center space-x-4 my-6">
        <div>
          <label for="course" class="mr-2 font-semibold">Select Course:</label>
          <select
            id="course"
            v-model="selectedCourse"
            @change="fetchLogList"
            class="p-2 border border-gray-400 rounded bg-gray-100 focus:outline-none"
          >
            <option disabled value="">Please select a course</option>
            <option
              v-for="course in courses"
              :key="course.id"
              :value="course.id"
            >
              {{ course.id }}
            </option>
          </select>
        </div>

        <div v-if="isAdmin">
          <label for="search-student" class="mr-2 font-semibold"
            >Student ID:</label
          >
          <input
            id="search-student"
            v-model="searchStudentId"
            @keyup.enter="fetchLogList"
            type="text"
            placeholder="Please enter student ID"
            class="p-2 border border-gray-400 rounded bg-gray-100 focus:outline-none"
          />
          <button
            @click="fetchLogList"
            class="ml-2 p-2 border border-gray-500 text-gray-500 rounded transition-colors duration-200 hover:bg-gray-100 transform hover:scale-105"
          >
            Search
          </button>
        </div>
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
          v-html="sanitizedContent"
        ></div>
        <pre
          v-else
          class="border border-gray-300 p-4 bg-white rounded overflow-x-auto whitespace-pre-wrap text-sm"
          >{{ fileContent }}</pre
        >
      </div>

      <div v-if="error" class="mt-4 text-red-500">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import DOMPurify from "dompurify";
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
    const searchStudentId = ref("");

    const jwtPayload = computed(() => {
      if (!authStore.token) return {};
      try {
        const base64Payload = authStore.token.split(".")[1];
        return JSON.parse(atob(base64Payload));
      } catch (e) {
        return {};
      }
    });

    const isAdmin = computed(() => jwtPayload.value.admin === true);
    const studentId = computed(() => jwtPayload.value.sub || "");

    const isHTML = computed(() => {
      return selectedLogFile.value.toLowerCase().endsWith(".html");
    });

    const sanitizedContent = computed(() => {
      if (!isHTML.value || !fileContent.value) {
        return "";
      }
      return DOMPurify.sanitize(fileContent.value, {
        USE_PROFILES: { html: true },
      });
    });

    watch(selectedCourse, () => {
      fileContent.value = "";
      selectedLogFile.value = "";
      error.value = "";
    });

    const fetchCourses = async () => {
      try {
        const response = await axios.get(`${apiBase}/courses`, {
          headers: { Authorization: `Bearer ${authStore.token}` },
        });
        courses.value = response.data;
      } catch (err) {
        console.error("Failed to fetch courses", err);
        error.value = "Failed to fetch courses.";
      }
    };

    const fetchLogList = async () => {
      if (!selectedCourse.value) {
        error.value = "Please select a course.";
        return;
      }
      error.value = "";
      logList.value = [];
      fileContent.value = "";
      selectedLogFile.value = "";

      try {
        let url = `${apiBase}/courses/${selectedCourse.value}/logs`;
        if (isAdmin.value && searchStudentId.value) {
          url += `?student_id=${searchStudentId.value}`;
        }

        const response = await axios.get(url, {
          headers: { Authorization: `Bearer ${authStore.token}` },
        });
        if (Array.isArray(response.data)) {
          if (response.data.length === 0) {
            error.value = isAdmin.value
              ? "No logs found for that student ID."
              : `No logs found for student id: ${studentId.value}.`;
          } else {
            logList.value = response.data;
          }
        } else {
          error.value = "Unexpected response data.";
        }
      } catch (err) {
        console.error("Failed to fetch log list", err);
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
      error.value = "";

      try {
        const response = await axios.get(
          `${apiBase}/courses/${selectedCourse.value}/logs/${logFile}`,
          {
            headers: { Authorization: `Bearer ${authStore.token}` },
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
      searchStudentId,
      isAdmin,
      studentId,
      isHTML,
      sanitizedContent,
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
