<template>
  <q-layout>
    <q-page-container>
      <q-page class="flex bg-image flex-center">
        <q-card v-bind:style="$q.screen.lt.sm?{'width': '80%'}:{'width':'30%'}">
          <q-card-section>
            <div class="text-center q-pt-lg">
              <div class="col text-h4 ellipsis">Tactical Offsite</div>
            </div>
          </q-card-section>
          <q-card-section>
            <q-form @submit.prevent="onSubmit" class="q-gutter-md">
              <q-input
                filled
                v-model="credentials.username"
                label="Username"
                lazy-rules
                :rules="[ val => val && val.length > 0 || 'This field is required']"
              />

              <q-input
                type="password"
                filled
                v-model="credentials.password"
                label="Password"
                lazy-rules
                :rules="[ val => val && val.length > 0 || 'This field is required']"
              />

              <div>
                <q-btn label="Login" type="submit" color="primary" class="full-width" />
              </div>
            </q-form>
          </q-card-section>
        </q-card>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script>
import mixins from "../mixins/mixins";

export default {
  name: "Login",
  mixins: [mixins],
  data() {
    return {
      credentials: {},
      prompt: false
    };
  },

  methods: {
    onSubmit() {
      this.$q.loading.show();
      this.$store
        .dispatch("retrieveToken", this.credentials)
        .then(response => {
          this.credentials = {};
          this.$q.loading.hide();
          this.$router.push({ name: "Dashboard" });
        })
        .catch(() => {
          this.credentials = {};
          this.$q.loading.hide();
        });
    }
  }
};
</script>

<style>
.bg-image {
  background-image: linear-gradient(
    90deg,
    rgba(20, 20, 29, 1) 0%,
    rgba(38, 42, 56, 1) 49%,
    rgba(15, 18, 20, 1) 100%
  );
}
</style>