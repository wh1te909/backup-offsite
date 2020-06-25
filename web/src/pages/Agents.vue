<template>
  <q-page class="q-pa-sm">
    <div v-if="clients.length === 0">
      <q-inner-loading :showing="true">
        <q-spinner size="100px" color="primary" />
      </q-inner-loading>
    </div>
    <q-banner v-if="needNewVer" dense inline-actions rounded class="bg-red text-white">
      You are viewing an outdated version of this page.
      <q-btn @click="getNewVer" flat label="Click here to refresh" />
    </q-banner>
    <div
      v-else
      v-for="client in clients"
      :key="client.name"
      class="q-mb-md q-ml-md q-mr-md q-pa-md"
    >
      <div class="text-h4 text-weight-bold q-mb-md">{{ client.name }}</div>
      <div v-for="agent in client.agents" :key="agent.id" class="col-12">
        <q-card class="q-pa-md q-mb-md">
          <q-card-section class="q-pt-none">
            <div class="text-h6 text-grey-8">{{ agent.hostname }}</div>
          </q-card-section>

          <q-card-section class="q-pa-none">
            <div class="row">
              <!-- settings -->
              <div class="col-2">
                <AgentSettings :agent="agent" />
              </div>
              <!-- summary -->
              <div class="col-4">
                <AgentSummary :agent="agent" @edited="getClients(true)" />
              </div>
              <!-- actions -->
              <div class="col">
                <div class="row q-pa-xs q-gutter-xs q-mb-md">
                  <!-- start / stop / view offsites -->
                  <q-btn
                    align="right"
                    :loading="agent.offsite_running"
                    :disable="agent.offsite_running"
                    color="blue-14"
                    @click="startOffsite(agent.id)"
                  >
                    Start Offsite
                    <template v-slot:loading>
                      <q-spinner-bars class="q-mr-sm" size="md" align="left" />Offsiting
                    </template>
                  </q-btn>
                  <q-btn
                    v-show="agent.offsite_running"
                    color="positive"
                    @click="viewProgress(agent.id)"
                    icon="visibility"
                  />
                  <q-btn
                    v-show="agent.offsite_running"
                    color="negative"
                    @click="stopOffsite(agent.id)"
                    label="Stop"
                  />
                </div>
                <!-- start backup -->
                <div class="row q-pa-xs q-gutter-xs q-mb-md">
                  <q-btn-dropdown
                    align="right"
                    v-show="!agent.backup_running"
                    color="purple-6"
                    label="Start a Backup"
                  >
                    <q-list>
                      <q-item clickable v-close-popup @click="startVeeamBackup(agent.id, 'backup')">
                        <q-item-section>
                          <q-item-label>Incremental</q-item-label>
                        </q-item-section>
                      </q-item>

                      <q-item
                        clickable
                        v-close-popup
                        @click="startVeeamBackup(agent.id, 'activefull')"
                      >
                        <q-item-section>
                          <q-item-label>Differential Merge</q-item-label>
                        </q-item-section>
                      </q-item>

                      <q-item
                        clickable
                        v-close-popup
                        @click="startVeeamBackup(agent.id, 'standalone')"
                      >
                        <q-item-section>
                          <q-item-label>Standalone Full</q-item-label>
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </q-btn-dropdown>
                  <q-btn
                    v-show="agent.backup_running"
                    disable
                    loading
                    color="purple-6"
                    style="width: 150px"
                  >
                    <template v-slot:loading>
                      <q-spinner-bars size="md" class="on-left" />Backing up
                    </template>
                  </q-btn>
                </div>
              </div>
              <!-- pause / enable -->
              <div class="col-2">
                <div class="row q-pa-xs q-gutter-xs q-mb-md">
                  <q-toggle
                    v-model="agent.offsites_enabled"
                    :label="agent.offsites_enabled ? 'Offsites Enabled' : 'Offsites Paused'"
                    @input="toggleOffsites(agent.id, agent.offsites_enabled)"
                    color="blue-14"
                  />
                </div>
                <div class="row q-pa-xs q-gutter-xs q-mb-md">
                  <q-toggle
                    v-model="agent.backups_enabled"
                    :label="agent.backups_enabled ? 'Backups Enabled' : 'Backups Paused'"
                    @input="toggleBackups(agent.id, agent.backups_enabled)"
                    color="purple-6"
                  />
                </div>
              </div>
            </div>
          </q-card-section>
        </q-card>
      </div>
    </div>
    <!-- show progress dialog -->
    <q-dialog v-model="showViewProgress">
      <ViewProgress
        @close="showViewProgress = false; progressInfo = null; progressHostname = null"
        :progressInfo="progressInfo"
        :progressHostname="progressHostname"
      />
    </q-dialog>
  </q-page>
</template>

<script>
import mixins from "../mixins/mixins";
import AgentSummary from "../components/AgentSummary";
import AgentSettings from "../components/AgentSettings";
import ViewProgress from "../components/ViewProgress";

import { mapGetters } from "vuex";

export default {
  name: "Agents",
  components: { ViewProgress, AgentSummary, AgentSettings },
  mixins: [mixins],
  data() {
    return {
      progress: false,
      pollClients: null,
      clients: [],
      progressInfo: null,
      progressHostname: null,
      showViewProgress: false
    };
  },
  computed: {
    ...mapGetters(["needNewVer"])
  },
  methods: {
    getClients(showLoading = false) {
      if (showLoading) {
        this.$q.loading.show();
      }
      this.$axios.get("/core/clients/").then(r => {
        for (let i = 0; i < r.data.length; i++) {
          r.data[i].agents.sort((a, b) =>
            a.hostname.toLowerCase() > b.hostname.toLowerCase() ? 1 : -1
          );
        }

        this.clients = r.data;

        if (showLoading) {
          this.$q.loading.hide();
        }
      });
    },
    liveClients() {
      this.pollClients = setInterval(() => {
        this.getClients();
        this.$store.dispatch("checkVer");
      }, 65 * 1000);
    },
    getNewVer() {
      this.$store.dispatch("getNewVer");
    },

    startVeeamBackup(pk, mode) {
      this.$q.loading.show({ message: "Contacting agent...please wait..." });
      const data = { pk: pk, mode: mode };
      this.$axios
        .post("/core/startbackup/", data)
        .then(r => {
          this.getClients(true);
          this.notifySuccess(r.data);
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError(e.response.data);
        });
    },
    startOffsite(pk) {
      this.$q.loading.show();
      this.$axios
        .get(`/core/${pk}/start/`)
        .then(r => {
          this.getClients(true);
          this.notifySuccess(r.data);
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError(e.response.data);
        });
    },
    stopOffsite(pk) {
      this.$q.loading.show();
      this.$axios
        .get(`/core/${pk}/cancel/`)
        .then(r => {
          this.getClients(true);
          this.notifySuccess(r.data);
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError(e.response.data);
        });
    },
    viewProgress(pk, hostname) {
      this.$q.loading.show();
      this.$axios
        .get(`/core/${pk}/viewprogress/`)
        .then(r => {
          this.$q.loading.hide();
          this.progressInfo = r.data;
          this.progressHostname = hostname;
          this.showViewProgress = true;
        })
        .catch(e => {
          this.$q.loading.hide();
          this.notifyError(e.response.data);
        });
    },
    toggleOffsites(pk, val) {
      const data = { pk: pk, val: val };
      this.$axios
        .patch("/core/toggleoffsite", data)
        .then(r => {
          this.getClients();
          this.notifySuccess(r.data);
        })
        .catch(() => {
          this.notifyError("Something went wrong");
        });
    },
    toggleBackups(pk, val) {
      const data = { pk: pk, val: val };
      this.$axios
        .patch("/core/togglebackup", data)
        .then(r => {
          this.getClients();
          this.notifySuccess(r.data);
        })
        .catch(() => {
          this.notifyError("Something went wrong");
        });
    }
  },
  created() {
    this.getClients();
    this.$store.dispatch("checkVer");
  },
  mounted() {
    this.liveClients();
  },
  beforeDestroy() {
    clearInterval(this.pollClients);
  }
};
</script>
