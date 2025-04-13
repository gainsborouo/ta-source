<template>
  <div class="text-gray-800 p-6">
    <div class="max-w-7xl mx-auto">
      <h2
        class="text-3xl font-bold mb-6 text-center tracking-wide border-b border-gray-300 pb-6"
      >
        Log Viewer
      </h2>

      <div
        class="flex flex-col md:flex-row md:items-center space-y-4 md:space-y-0 md:space-x-4 my-6"
      >
        <div class="w-full md:w-auto">
          <label for="course" class="mr-2 font-semibold">Course:</label>
          <select
            id="course"
            v-model="selectedCourse"
            @change="fetchLogList"
            class="w-full md:w-auto p-2 border border-gray-400 rounded bg-gray-100 focus:outline-none"
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

        <div v-if="isAdmin" class="w-full md:w-auto">
          <div class="flex flex-col md:flex-row md:items-center">
            <label
              for="search-student"
              class="font-semibold md:mr-2"
              >Student&nbsp;ID:</label
            >
            <div class="flex flex-row items-center space-x-2">
              <input
                id="search-student"
                v-model="searchStudentId"
                @keyup.enter="fetchLogList"
                type="text"
                placeholder="Please enter a student ID"
                class="flex-1 p-2 border border-gray-400 rounded bg-gray-100 focus:outline-none"
              />
              <button
                @click="fetchLogList"
                class="p-2 border border-gray-500 text-gray-500 rounded transition-colors duration-200 hover:bg-gray-100 transform hover:scale-105"
              >
                Search
              </button>
            </div>
          </div>
        </div>
      </div>

      <div class="md:flex md:h-[calc(100vh-20rem)]">
        <div class="md:w-1/3 pr-4 h-full overflow-y-auto">
          <ul id="logList" class="list-none p-0">
            <li
              v-for="log in logList"
              :key="log"
              @click="loadLog(log)"
              :class="[
                'p-2 mb-2 first:mt-0 last:mb-0 border-l-4 rounded cursor-pointer transition-colors duration-200 bg-gray-100',
                log === selectedLogFile
                  ? 'border-cyan-700 bg-gray-200'
                  : 'border-transparent hover:bg-gray-200',
              ]"
            >
              {{ log }}
            </li>
          </ul>
          <div v-if="error" class="mt-4 text-red-500">{{ error }}</div>
        </div>

        <div
          v-if="logList.length"
          class="hidden md:block flex-1 h-full overflow-hidden"
        >
          <div
            class="border border-gray-300 bg-gray-100 rounded h-full w-full overflow-auto"
          >
            <div class="p-4 h-full flex items-start">
              <template v-if="fileContent">
                <div
                  v-if="isHTML"
                  class="restore-padding break-words"
                  v-html="sanitizedContent"
                ></div>
                <pre v-else class="whitespace-pre-wrap break-all text-sm">{{
                  fileContent
                }}</pre>
              </template>
              <template v-else>
                <p class="text-gray-400 select-none">
                  Please select a log file from the left
                </p>
              </template>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div
      v-if="isModalOpen"
      class="fixed inset-0 z-40 bg-white md:hidden overflow-hidden"
    >
      <div
        class="sticky top-0 z-50 bg-white border-b border-gray-200 p-4 flex justify-between items-center"
      >
        <span class="text-base font-medium truncate max-w-[80%]">{{
          selectedLogFile
        }}</span>
        <div class="flex items-center">
          <button
            class="text-gray-600 hover:text-gray-800 mr-4"
            @click="downloadLog"
            title="Download log file"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
              />
            </svg>
          </button>
          <button
            class="text-3xl leading-none text-gray-600 hover:text-gray-800"
            @click="closeModal"
          >
            &times;
          </button>
        </div>
        <!-- <button
          class="text-3xl leading-none text-gray-600 hover:text-gray-800"
          @click="closeModal"
        >
          &times;
        </button> -->
      </div>
      <div
        class="absolute inset-x-0 bottom-0 top-[5rem] overflow-y-auto border border-gray-300 bg-gray-100 m-4 mt-0 rounded p-4"
      >
        <div
          v-if="isHTML"
          class="restore-padding break-words"
          v-html="sanitizedContent"
        ></div>
        <pre v-else class="whitespace-pre-wrap break-all text-sm">{{
          fileContent
        }}</pre>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import DOMPurify from "dompurify";
import { computed, ref, watch, onMounted } from "vue";
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
    const isModalOpen = ref(false);

    const jwtPayload = computed(() => {
      if (!authStore.token) return {};
      try {
        return JSON.parse(atob(authStore.token.split(".")[1]));
      } catch {
        return {};
      }
    });

    const isAdmin = computed(() => jwtPayload.value.admin === true);
    const studentId = computed(() => jwtPayload.value.sub || "");
    const isHTML = computed(() =>
      selectedLogFile.value.toLowerCase().endsWith(".html")
    );

    const sanitizedContent = computed(() =>
      isHTML.value && fileContent.value
        ? DOMPurify.sanitize(fileContent.value, {
            USE_PROFILES: { html: true },
          })
        : ""
    );

    /* ---------- helpers ---------- */
    const clearSelection = () => {
      selectedLogFile.value = "";
      fileContent.value = "";
    };

    const isMobile = () => window.innerWidth < 768;

    /* ---------- API ---------- */
    const fetchCourses = async () => {
      try {
        const { data } = await axios.get(`${apiBase}/courses`, {
          headers: { Authorization: `Bearer ${authStore.token}` },
        });
        courses.value = data;
      } catch (err) {
        console.error(err);
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
      clearSelection();
      isModalOpen.value = false;

      try {
        let url = `${apiBase}/courses/${selectedCourse.value}/logs`;
        if (isAdmin.value && searchStudentId.value)
          url += `?student_id=${searchStudentId.value}`;

        const { data } = await axios.get(url, {
          headers: { Authorization: `Bearer ${authStore.token}` },
        });

        if (Array.isArray(data)) {
          data.length
            ? (logList.value = data)
            : (error.value = isAdmin.value
                ? "No logs found for that student ID."
                : `No logs found for student id: ${studentId.value}.`);
        } else {
          error.value = "Unexpected response data.";
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
        clearSelection();
        return;
      }

      selectedLogFile.value = logFile;
      error.value = "";
      try {
        const { data } = await axios.get(
          `${apiBase}/courses/${selectedCourse.value}/logs/${logFile}`,
          {
            headers: { Authorization: `Bearer ${authStore.token}` },
          }
        );
        fileContent.value = data.content;
        isModalOpen.value = isMobile();
      } catch (err) {
        console.error(err);
        error.value =
          (err.response && err.response.data.detail) ||
          "Failed to fetch log content.";
      }
    };

    const closeModal = () => {
      isModalOpen.value = false;
      clearSelection();
    };

    /* ---------- watchers ---------- */
    watch(selectedCourse, () => {
      clearSelection();
      error.value = "";
      isModalOpen.value = false;
    });

    onMounted(fetchCourses);

    return {
      courses,
      selectedCourse,
      logList,
      fileContent,
      error,
      selectedLogFile,
      searchStudentId,
      isAdmin,
      isHTML,
      sanitizedContent,
      fetchLogList,
      loadLog,
      isModalOpen,
      closeModal,
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
