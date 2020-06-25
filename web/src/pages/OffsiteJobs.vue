<template>
  <q-page v-if="data.length === 0" class="q-pa-sm">
    <q-inner-loading :showing="true">
      <q-spinner size="100px" color="primary" />
    </q-inner-loading>
  </q-page>
  <q-page v-else class="q-pa-sm">
    <q-banner v-if="needNewVer" dense inline-actions rounded class="bg-red text-white">
      You are viewing an outdated version of this page.
      <q-btn @click="getNewVer" flat label="Click here to refresh" />
    </q-banner>
    <q-card class="q-mt-lg">
      <q-card-section>
        <div class="text-h6 text-grey-8">Offsite Jobs</div>
      </q-card-section>
      <q-card-section class="q-pa-none">
        <q-table
          dense
          :data="data"
          :columns="columns"
          row-key="id"
          :visible-columns="visibleColumns"
          :pagination.sync="pagination"
          binary-state-sort
        >
          <template slot="body" slot-scope="props" :props="props">
            <q-tr>
              <q-td>{{ props.row.hostname }}</q-td>
              <q-td>{{ props.row.client }}</q-td>
              <q-td v-if="props.row.status === 'cancelled'">
                <q-icon name="error" color="negative" size="sm">
                  <q-tooltip>{{ props.row.status }}</q-tooltip>
                </q-icon>
              </q-td>
              <q-td v-else-if="props.row.status === 'completed'">
                <q-icon name="check_circle" color="positive" size="sm">
                  <q-tooltip>{{ props.row.status }}</q-tooltip>
                </q-icon>
              </q-td>
              <q-td v-else-if="props.row.status === 'running'">
                <q-linear-progress indeterminate>
                  <q-tooltip>Job is currently running</q-tooltip>
                </q-linear-progress>
              </q-td>
              <q-td>{{ props.row.started }}</q-td>
              <q-td>{{ props.row.finished }}</q-td>
              <q-td>
                <q-btn
                  dense
                  size="sm"
                  push
                  color="primary"
                  label="View Details"
                  @click="viewProgress(props.row.id, props.row.hostname)"
                />
              </q-td>
            </q-tr>
          </template>
        </q-table>
      </q-card-section>
    </q-card>
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
import ViewProgress from "../components/ViewProgress";
import { mapGetters } from "vuex";

export default {
  name: "OffsiteJobs",
  components: { ViewProgress },
  mixins: [mixins],
  data() {
    return {
      data: [],
      pollJobs: null,
      progressInfo: null,
      progressHostname: null,
      showViewProgress: false,
      visibleColumns: [
        "hostname",
        "client",
        "status",
        "started",
        "finished",
        "output"
      ],
      columns: [
        { name: "id", field: "id" },
        { name: "pid", field: "pid" },
        { name: "agent", field: "agent" },
        {
          name: "hostname",
          label: "Agent",
          field: "hostname",
          align: "left",
          sortable: true
        },
        {
          name: "client",
          label: "Client",
          field: "client",
          align: "left",
          sortable: true
        },
        {
          name: "status",
          label: "Status",
          field: "status",
          align: "left",
          sortable: true
        },
        {
          name: "started",
          label: "Started",
          field: "started",
          align: "left",
          sortable: true
        },
        {
          name: "finished",
          label: "Finished",
          field: "finished",
          align: "left",
          sortable: true
        },
        {
          name: "output",
          label: "Output",
          field: "output",
          align: "left",
          sortable: false
        }
      ],
      pagination: {
        sortBy: "id",
        descending: true,
        rowsPerPage: 30
      }
    };
  },
  computed: {
    ...mapGetters(["needNewVer"])
  },
  methods: {
    getJobs() {
      this.$axios.get("/core/offsitejobs/").then(r => {
        this.data = r.data;
      });
    },
    liveJobs() {
      this.pollJobs = setInterval(() => {
        this.getJobs();
        this.$store.dispatch("checkVer");
      }, 30000);
    },
    viewProgress(pk, name) {
      this.$q.loading.show();
      this.$axios
        .get(`/core/${pk}/viewoffsiteoutput/`)
        .then(r => {
          this.progressInfo = r.data;
          this.progressHostname = name;
          this.showViewProgress = true;
          this.$q.loading.hide();
        })
        .catch(() => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong");
        });
    },
    getNewVer() {
      this.$store.dispatch("getNewVer");
    }
  },
  created() {
    this.getJobs();
    this.$store.dispatch("checkVer");
  },
  mounted() {
    this.liveJobs();
  },
  beforeDestroy() {
    clearInterval(this.pollJobs);
  }
};
</script>
