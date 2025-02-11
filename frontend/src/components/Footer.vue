<template>
  <div class="px-6">
    <footer
      class="text-center text-gray-700 text-xs p-2 border-t border-gray-500 md:text-sm md:p-3"
    >
      <p>© {{ currentYear }} Ting-Wei Chou</p>
    </footer>
  </div>
</template>

<script>
export default {
  name: "Footer",
  data() {
    return {
      currentYear: new Date().getFullYear(),
    };
  },
};
</script>
