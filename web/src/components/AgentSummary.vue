<template>
  <q-item>
    <q-item-section>
      <!-- status size -->
      <q-item-label>
        <span class="text-overline text-subtitle1 text-uppercase text-grey-8 q-pa-sm">Sync Status:</span>
        <q-badge
          class="text-subtitle2"
          :color="agent.raw_size === agent.raw_onsite_size ? 'positive' : 'negative'"
        >{{ agent.size }} / {{ agent.onsite_size }}</q-badge>
      </q-item-label>
      <!-- full backups -->
      <q-item-label>
        <span class="text-overline text-subtitle1 text-uppercase text-grey-8 q-pa-sm">Full backups:</span>
        <q-badge class="text-subtitle2" color="blue">{{ agent.details.full }}</q-badge>
      </q-item-label>
      <!-- incremental backups -->
      <q-item-label>
        <span
          class="text-overline text-subtitle1 text-uppercase text-grey-8 q-pa-sm"
        >Incremental backups:</span>
        <q-badge class="text-subtitle2" color="purple">{{ agent.details.inc }}</q-badge>
      </q-item-label>
    </q-item-section>
  </q-item>
</template>

<script>
export default {
  name: "AgentSummarry",
  props: ["agent"]
};
</script>