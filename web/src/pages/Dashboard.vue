<template>
  <q-page v-if="clients.length === 0" class="q-pa-sm">
    <q-inner-loading :showing="true">
      <q-spinner size="100px" color="primary" />
    </q-inner-loading>
  </q-page>
  <q-page v-else class="q-pa-sm">
    <q-banner v-if="needNewVer" dense inline-actions rounded class="bg-red text-white">
      You are viewing an outdated version of this page.
      <q-btn @click="getNewVer" flat label="Click here to refresh" />
    </q-banner>
    <!-- top cards -->
    <q-card class="bg-transparent no-shadow no-border">
      <q-card-section class="q-pa-none">
        <div class="row q-col-gutter-sm">
          <div class="col-md-3 col-sm-12 col-xs-12">
            <q-item style="background-color: #363636" class="q-pa-none q-ml-xs q-mr-xs">
              <q-item-section
                side
                style="background-color: gray"
                class="q-pa-lg q-mr-none text-white"
              >
                <q-icon name="signal_cellular_alt" size="24px"></q-icon>
              </q-item-section>
              <q-item-section class="q-pa-md q-ml-none text-white">
                <q-item-label class="text-white text-h6">{{ nettop }}</q-item-label>
                <q-item-label>Incoming transfer</q-item-label>
              </q-item-section>
            </q-item>
          </div>
          <div class="col-md-3 col-sm-12 col-xs-12">
            <q-item style="background-color: #363636" class="q-pa-none q-ml-xs">
              <q-item-section
                side
                style="background-color: gray"
                class="q-pa-lg q-mr-none text-white"
              >
                <q-icon name="storage" color="white" size="24px"></q-icon>
              </q-item-section>
              <q-item-section class="q-pa-md q-ml-none text-white">
                <q-item-label class="text-white text-h6">{{ used }} / {{ total }}</q-item-label>
                <q-item-label>Storage</q-item-label>
              </q-item-section>
            </q-item>
          </div>
          <div class="col-md-3 col-sm-12 col-xs-12">
            <q-item style="background-color: #363636" class="q-pa-none q-ml-xs">
              <q-item-section
                side
                style="background-color: gray"
                class="q-pa-lg q-mr-none text-white"
              >
                <q-icon name="fas fa-server" size="24px"></q-icon>
              </q-item-section>
              <q-item-section class="q-pa-md q-ml-none text-white">
                <q-item-label class="text-white text-h6 text-weight-bolder">{{ agentCount }}</q-item-label>
                <q-item-label>Agents</q-item-label>
              </q-item-section>
            </q-item>
          </div>
          <div class="col-md-3 col-sm-12 col-xs-12">
            <q-item style="background-color: #363636" class="q-pa-none q-ml-xs">
              <q-item-section
                side
                style="background-color: gray"
                class="q-pa-lg q-mr-none text-white"
              >
                <q-icon name="apartment" size="24px"></q-icon>
              </q-item-section>
              <q-item-section class="q-pa-md q-ml-none text-white">
                <q-item-label class="text-white text-h6 text-weight-bolder">{{ clientCount }}</q-item-label>
                <q-item-label>Clients</q-item-label>
              </q-item-section>
            </q-item>
          </div>
        </div>
      </q-card-section>
    </q-card>
    <!-- middle cards -->
    <div class="row q-col-gutter-sm q-py-sm">
      <!-- status-->
      <div class="col-lg-12 col-md-12 col-sm-12 col-xs-12">
        <q-card>
          <q-card-section>
            <div class="text-h6 text-grey-8">Replication Status</div>
          </q-card-section>
          <q-separator />
          <q-card-section style="max-height: 72vh" class="scroll">
            <q-list dense>
              <template v-for="client in clients">
                <q-item-label header :key="client.name">{{ client.name }}</q-item-label>
                <q-item v-for="agent in client.agents" :key="agent.id" class="q-my-sm">
                  <!-- icon -->
                  <q-item-section side>
                    <q-icon name="cloud" v-if="agent.size === agent.onsite_size" color="positive" />
                    <q-icon name="cloud" v-else color="warning" />
                  </q-item-section>
                  <!-- hostname -->
                  <q-item-section>
                    <q-item-label>{{ agent.hostname }}</q-item-label>
                  </q-item-section>
                  <!-- size of size -->
                  <q-item-section>
                    <q-item-label>{{ agent.size }} / {{ agent.onsite_size }} synced</q-item-label>
                  </q-item-section>
                  <!-- last sync or live bar -->
                  <q-item-section v-if="agent.last_offsite_job === 'inprogress'">
                    <q-linear-progress size="xl" indeterminate color="info" class="q-mt-sm" />
                  </q-item-section>
                  <q-item-section v-else>
                    <q-item-label class="text-caption">{{ agent.last_offsite_job }}</q-item-label>
                  </q-item-section>
                  <!-- percent and progress meter -->
                  <q-item-section>
                    <q-linear-progress
                      v-if="agent.size === agent.onsite_size"
                      stripe
                      size="xl"
                      :value="1"
                      color="positive"
                      class="q-mt-sm"
                    >
                      <div class="absolute-center flex flex-center text-black">100%</div>
                    </q-linear-progress>
                    <q-linear-progress
                      v-else
                      stripe
                      :value="percentSynced(agent.size, agent.onsite_size)"
                      size="xl"
                      color="warning"
                      track-color="primary"
                      class="q-mt-sm"
                    >
                      <div
                        class="absolute-center flex flex-center text-black"
                      >{{ progressLabel(agent.size, agent.onsite_size) }}</div>
                    </q-linear-progress>
                  </q-item-section>
                </q-item>
              </template>
            </q-list>
          </q-card-section>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: "PageIndex",
  data() {
    return {
      ws: null,
      used: null,
      total: null,
      nettop: null,
      agentCount: null,
      clientCount: null,
      pollStorage: null,
      clients: []
    };
  },
  computed: {
    ...mapGetters(["needNewVer"]),
    wsUrl() {
      return this.$axios.defaults.baseURL.split("://")[1];
    },
    token() {
      return this.$store.state.token;
    }
  },
  methods: {
    setupWS() {
      console.log("Starting websocket");
      this.ws = new WebSocket(
        `ws://${this.wsUrl}/ws/nettop/?access_token=${this.token}`
      );

      this.ws.onopen = e => {
        console.log("Connected to ws");
      };

      this.ws.onmessage = e => {
        this.nettop = e.data;
      };

      this.ws.onclose = e => {
        console.log(`Closed code: ${e.code}`);
        if (e.code !== 1000) {
          setTimeout(() => {
            this.setupWS();
          }, 5 * 1000);
        }
      };

      this.ws.onerror = err => {
        console.log(`ERROR! Code: ${err.code}`);
        this.ws.close();
      };
    },
    getInfo() {
      this.$axios.get("/core/info/").then(r => {
        this.used = r.data.used;
        this.total = r.data.total;
        this.agentCount = r.data.agents;
        this.clientCount = r.data.clients;
      });
    },
    progressLabel(size, onsite) {
      let s = size.replace(/[^0-9.]/g, "");
      let o = onsite.replace(/[^0-9.]/g, "");
      let newSize;
      let newOnsite;

      if (size.endsWith("GB")) {
        newSize = s;
      } else if (size.endsWith("TB")) {
        newSize = s * 1000;
      }

      if (onsite.endsWith("GB")) {
        newOnsite = o;
      } else if (onsite.endsWith("TB")) {
        newOnsite = o * 1000;
      }

      return ((newSize / newOnsite) * 100).toFixed(2) + "%";
    },
    percentSynced(size, onsite) {
      let s = size.replace(/[^0-9.]/g, "");
      let o = onsite.replace(/[^0-9.]/g, "");

      let newSize;
      let newOnsite;

      if (size.endsWith("GB")) {
        newSize = s;
      } else if (size.endsWith("TB")) {
        newSize = s * 1000;
      }

      if (onsite.endsWith("GB")) {
        newOnsite = o;
      } else if (onsite.endsWith("TB")) {
        newOnsite = o * 1000;
      }

      return newSize / newOnsite;
    },
    getNewVer() {
      this.$store.dispatch("getNewVer");
    },
    getClients() {
      this.$axios.get("/core/clients/").then(r => {
        for (let i = 0; i < r.data.length; i++) {
          r.data[i].agents.sort((a, b) =>
            a.hostname.toLowerCase() > b.hostname.toLowerCase() ? 1 : -1
          );
        }
        this.clients = r.data;
      });
    },
    liveStorage() {
      this.pollStorage = setInterval(() => {
        this.getInfo();
        this.getClients();
        this.$store.dispatch("checkVer");
      }, 15 * 1000);
    }
  },
  created() {
    this.setupWS();
    this.getInfo();
    this.getClients();
    this.$store.dispatch("checkVer");
  },
  mounted() {
    this.liveStorage();
  },
  beforeDestroy() {
    this.ws.close();
    clearInterval(this.pollStorage);
  }
};
</script>
