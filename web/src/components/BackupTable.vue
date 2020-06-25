<template>
  <q-card style="min-width: 50vw" class="q-pa-xs">
    <q-card-section>
      <div class="row items-center">
        <div class="text-h6">{{ agent.hostname }} - {{ agent.client_name }}</div>

        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
      <div class="row text-caption text-weight-medium">On-site backup files</div>
    </q-card-section>

    <q-separator />

    <q-card-section>
      <q-table
        dense
        :data="agent.details.files"
        :columns="columns"
        row-key="name"
        :pagination.sync="pagination"
        binary-state-sort
      >
        <template slot="body" slot-scope="props" :props="props">
          <q-tr>
            <q-td>{{ props.row.name }}</q-td>
            <q-td v-if="props.row.type === 'inc'">
              <q-badge color="purple">Incremental</q-badge>
            </q-td>
            <q-td v-else-if="props.row.type === 'full'">
              <q-badge color="blue">Full</q-badge>
            </q-td>
            <q-td v-else>
              <q-badge color="primary">Unknown</q-badge>
            </q-td>
            <q-td>{{ props.row.size }}</q-td>
            <q-td>{{ formatMtime(props.row.mtime) }}</q-td>
          </q-tr>
        </template>
      </q-table>
    </q-card-section>
  </q-card>
</template>

<script>
import { date } from "quasar";

export default {
  name: "BackupTable",
  props: ["agent"],
  data() {
    return {
      columns: [
        {
          name: "name",
          label: "Name",
          field: "name",
          align: "left",
          sortable: true
        },
        {
          name: "type",
          label: "Type",
          field: "type",
          align: "left",
          sortable: true
        },
        {
          name: "size",
          label: "Size",
          field: "size",
          align: "left",
          sortable: true
        },
        {
          name: "mtime",
          label: "Date",
          field: "mtime",
          align: "left",
          sortable: true
        }
      ],
      pagination: {
        sortBy: "mtime",
        descending: true,
        rowsPerPage: 20
      }
    };
  },
  methods: {
    formatMtime(timestamp) {
      return date.formatDate(timestamp * 1000, "MMM Do, YYYY h:mm A");
    }
  },
  beforeDestroy() {
    this.$emit("close");
  }
};
</script>