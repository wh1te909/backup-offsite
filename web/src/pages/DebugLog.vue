<template>
  <q-page class="q-pa-sm">
    <q-banner v-if="needNewVer" dense inline-actions rounded class="bg-red text-white">
      You are viewing an outdated version of this page.
      <q-btn @click="getNewVer" flat label="Click here to refresh" />
    </q-banner>
    <q-card>
      <q-card-section>
        <q-btn @click="getLog" dense flat push icon="refresh" />
      </q-card-section>
        <q-card-section style="max-height: 80vh" class="scroll">
          <pre>{{ log }}</pre>
        </q-card-section>
    </q-card>
  </q-page>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: "DebugLog",
  data() {
    return {
      log: null,
      pollLog: null,
    };
  },
  computed: {
    ...mapGetters(["needNewVer"])
  },
  methods: {
    getLog() {
      this.$q.loading.show();
      this.$axios.get("/core/debuglog/").then(r => {
        this.$q.loading.hide();
        this.log = r.data;
      }).catch(e => {
        this.$q.loading.hide();
        this.notifyError("Something went wrong")
      })
    },
    liveLog() {
      this.pollLog = setInterval(() => {
        this.$store.dispatch("checkVer");
      }, 60 * 1000);
    },
    getNewVer() {
      this.$store.dispatch("getNewVer");
    }
  },
  created() {
    this.getLog();
    this.$store.dispatch("checkVer");
  },
  mounted() {
    this.liveLog();
  },
  beforeDestroy() {
    clearInterval(this.pollLog);
  }
};
</script>
