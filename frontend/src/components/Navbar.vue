<template>
  <TheDropDownNavbar>
    <template #logo>
      <TheDropDownNavbarLogo link="/" imageUrl="/images/icon.png">
        TA System
      </TheDropDownNavbarLogo>
    </template>
    <TheDropDownItem link="/">Home</TheDropDownItem>

    <template v-if="!isLoggedIn">
      <TheDropDownItem link="/login">Login</TheDropDownItem>
    </template>

    <template v-if="isLoggedIn">
      <TheDropDownItem link="/logviewer">Log Viewer</TheDropDownItem>
      <TheDropDownMenu :text="studentId">
        <TheDropDownItem @click="logout">Logout</TheDropDownItem>
      </TheDropDownMenu>
    </template>
  </TheDropDownNavbar>
</template>

<script>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { authStore } from "../store/auth";
import {
  TheDropDownNavbar,
  TheDropDownMenu,
  TheDropDownItem,
  TheDropDownDivideBlock,
  TheDropDownNavbarLogo,
} from "vue3-dropdown-navbar";

export default {
  name: "Navbar",
  components: {
    TheDropDownNavbar,
    TheDropDownMenu,
    TheDropDownItem,
    TheDropDownDivideBlock,
    TheDropDownNavbarLogo,
  },
  setup() {
    const router = useRouter();
    const isLoggedIn = computed(() => !!authStore.token);
    const studentId = computed(() => {
      if (!authStore.token) return "";
      try {
        const payload = JSON.parse(atob(authStore.token.split(".")[1]));
        return payload.sub;
      } catch (error) {
        return "";
      }
    });

    const logout = () => {
      authStore.setToken(null);
      router.push({ name: "Home" });
    };

    return { isLoggedIn, studentId, logout };
  },
};
</script>

<style scoped></style>
