<template>
  <div class="fixed-center text-center">
    <p class="text-faded">Your session has expired</p>
    <q-btn color="info" style="width:200px;" to="/Login" label="Login" />
  </div>
</template>

<script>
export default {
  name: "SessionExpired",
  created() {
    this.$store.dispatch("destroyToken");
  }
};
</script>
