<template>
  <q-card style="min-width: 50vw" class="q-pa-xs">
    <q-card-section>
      <div class="row items-center">
        <div class="text-h6">{{ progressHostname }}</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section v-if="progressInfo" style="max-height: 50vh" class="scroll">
      <pre v-html="Object.freeze(progressInfo)"></pre>
    </q-card-section>
    <q-card-section v-else style="max-height: 50vh" class="scroll">
      <span class="text-h6">No output</span>
    </q-card-section>
  </q-card>
</template>

<script>
export default {
  name: "ViewProgress",
  props: ["progressInfo", "progressHostname"],
  methods: {
    convert(txt) {
      return txt.replace(/(?:\r\n|\r|\n)/g, "<br>");
    }
  },
  beforeDestroy() {
    this.$emit("close");
  }
};
</script>