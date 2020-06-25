<template>
  <q-list bordered separator>
    <!-- configure backups -->
    <q-item clickable v-ripple @click="showConfigureBackups = true">
      <q-item-section>
        <q-item-label class="text-blue-7">Configure Backups</q-item-label>
      </q-item-section>
    </q-item>
    <!-- configure offsites -->
    <q-item clickable v-ripple @click="showConfigureOffsites = true">
      <q-item-section>
        <q-item-label class="text-blue-7">Configure Offsites</q-item-label>
      </q-item-section>
    </q-item>
    <!-- view agent backups -->
    <q-item clickable v-ripple @click="showBackups(agent)">
      <q-item-section>
        <q-item-label class="text-blue-7">Show Backups</q-item-label>
      </q-item-section>
    </q-item>
    <!-- view offsite files -->
    <!-- <q-item clickable v-ripple @click="viewOffsiteDetails(agent)">
      <q-item-section>
        <q-item-label class="text-blue-7">Offsite Files</q-item-label>
      </q-item-section>
    </q-item>-->
    <q-dialog v-model="showBackupsTable">
      <BackupTable @close="showBackupsTable = false" :agent="agent" />
    </q-dialog>
    <!-- configure backups dialog -->
    <q-dialog v-model="showConfigureBackups" persistent>
      <ConfigureBackups :agent="agent" @close="showConfigureBackups = false" />
    </q-dialog>
    <!-- configure offsites dialog -->
    <q-dialog v-model="showConfigureOffsites" persistent>
      <ConfigureOffsites :agent="agent" @close="showConfigureOffsites = false" />
    </q-dialog>
  </q-list>
</template>

<script>
import mixins from "../mixins/mixins";
import BackupTable from "./BackupTable";
import ConfigureBackups from "../components/ConfigureBackups";
import ConfigureOffsites from "../components/ConfigureOffsites";
export default {
  name: "AgentSummarry",
  props: ["agent"],
  mixins: [mixins],
  components: { BackupTable, ConfigureBackups, ConfigureOffsites },
  data() {
    return {
      showBackupsTable: false,
      showConfigureBackups: false,
      showConfigureOffsites: false
    };
  },
  methods: {
    showBackups(agent) {
      this.showBackupsTable = true;
    }
  }
};
</script>