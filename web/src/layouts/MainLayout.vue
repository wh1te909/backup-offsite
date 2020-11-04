<template>
  <q-layout view="lHh Lpr lFf">
    <q-header elevated>
      <q-toolbar>
        <q-btn
          flat
          dense
          round
          @click="leftDrawerOpen = !leftDrawerOpen"
          icon="menu"
          aria-label="Menu"
        />

        <q-toolbar-title>Tactical Offsite</q-toolbar-title>

        <q-space />
        <!-- <q-toggle
          v-model="dark"
          color="yellow"
          label="Dark Mode"
          left-label
          @input="$q.dark.toggle(dark)"
        />-->
        <q-btn flat round dense icon="fas fa-sign-out-alt" to="/Expired" />
      </q-toolbar>
    </q-header>

    <q-drawer
      v-model="leftDrawerOpen"
      :width="200"
      show-if-above
      bordered
      content-class="bg-primary text-white"
    >
      <q-list>
        <q-item to="/" active-class="q-item-no-link-highlighting">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Dashboard</q-item-label>
          </q-item-section>
        </q-item>
        <q-item to="/Agents" active-class="q-item-no-link-highlighting">
          <q-item-section avatar>
            <q-icon name="fas fa-server" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Agents</q-item-label>
          </q-item-section>
        </q-item>
        <q-item to="/DebugLog" active-class="q-item-no-link-highlighting">
          <q-item-section avatar>
            <q-icon name="far fa-sticky-note" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Logs</q-item-label>
          </q-item-section>
        </q-item>
        <q-item to="/OffsiteJobs" active-class="q-item-no-link-highlighting">
          <q-item-section avatar>
            <q-icon name="fas fa-clipboard-list" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Offsite Jobs</q-item-label>
          </q-item-section>
        </q-item>
        <q-item to="/BackupJobs" active-class="q-item-no-link-highlighting">
          <q-item-section avatar>
            <q-icon name="fas fa-clipboard-list" />
          </q-item-section>
          <q-item-section>
            <q-item-label>Backup Jobs</q-item-label>
          </q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <q-page-container class="bg-grey-2">
      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  name: "MainLayout",
  data() {
    return {
      leftDrawerOpen: false,
      dark: true
    };
  },
  computed: {
    ...mapGetters(["userName"])
  },
  methods: {}
};
</script>
