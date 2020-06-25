<template>
  <q-card style="min-width: 35vw" class="q-pa-xs">
    <q-card-section>
      <div class="row items-center">
        <div class="text-h6">{{ agent.hostname }} - Offsite Settings</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="q-pa-md">
      <q-form @submit.prevent="editSettings" class="q-gutter-md">
        <div class="row">
          <div class="col q-pa-xs q-gutter-xs q-mb-md">
            <q-toggle
              v-model="offsite_managed"
              :label="offsite_managed ? 'Automatically keep offsites in sync' : 'Manually run offsites'"
              color="blue-14"
            />
          </div>
        </div>
        <div class="row q-pa-md">
          <q-badge color="blue-14" class="q-mb-xl">Business Hours</q-badge>

          <q-range
            v-model="day_hours"
            :min="0"
            :max="23"
            :step="1"
            :left-label-value="showNiceDate(day_hours.min)"
            :right-label-value="showNiceDate(day_hours.max)"
            label-always
            color="blue-14"
          />
        </div>
        <!-- business hours -->
        <div class="row q-mb-lg">
          <q-checkbox
            v-model="limit_during_day"
            color="blue-14"
            :label="limit_during_day ? 'Limit speed during business hours' : 'Unlimited speed during business hours'"
          />
        </div>
        <div class="row q-pa-md">
          <q-slider
            v-model="day_bwlimit"
            :disable="!limit_during_day"
            :min="100"
            :max="4000"
            :step="100"
            label
            :label-value="`${day_bwlimit / 125} Mb/s`"
            label-always
            color="blue-14"
          />
        </div>
        <!-- after hours -->

        <q-badge color="primary" class="q-mb-xl">After Hours</q-badge>
        <div class="row q-mb-lg">
          <q-checkbox
            v-model="limit_during_night"
            color="primary"
            :label="limit_during_night ? 'Limit speed during after hours' : 'Unlimited speed during after hours'"
          />
        </div>
        <div class="row q-pa-md">
          <q-slider
            v-model="night_bwlimit"
            :disable="!limit_during_night"
            :min="100"
            :max="4000"
            :step="100"
            label
            :label-value="`${night_bwlimit / 125} Mb/s`"
            label-always
            color="primary"
          />
        </div>
        <div class="row q-pa-md">
          <q-btn label="Save" type="submit" color="positive" />
          <q-btn label="Cancel" v-close-popup color="primary" flat class="q-ml-sm" />
        </div>
      </q-form>
    </q-card-section>
  </q-card>
</template>

<script>
import mixins from "../mixins/mixins";
import { date } from "quasar";
export default {
  name: "ConfigureOffsites",
  props: ["agent"],
  mixins: [mixins],
  data() {
    return {
      day_hours: {
        min: 0,
        max: 23
      },
      day_bwlimit: 100,
      night_bwlimit: 100,
      limit_during_day: true,
      limit_during_night: true,
      offsite_managed: true
    };
  },
  methods: {
    editSettings() {
      this.$q.loading.show();
      const data = {
        pk: this.agent.id,
        day_hours: this.day_hours,
        day_bwlimit: this.day_bwlimit,
        night_bwlimit: this.night_bwlimit,
        limit_during_day: this.limit_during_day,
        limit_during_night: this.limit_during_night,
        offsite_managed: this.offsite_managed
      };
      this.$axios
        .patch("/core/offsitesettings/", data)
        .then(r => {
          this.$q.loading.hide();
          this.$emit("close");
          this.notifySuccess(r.data);
        })
        .catch(() => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong");
        });
    },
    getSettings() {
      this.$axios.get(`/core/${this.agent.id}/offsitesettings/`).then(r => {
        this.offsite_managed = r.data.offsite_managed;
        this.day_hours.min = r.data.day_hours[0];
        this.day_hours.max = r.data.day_hours[1];
        this.day_bwlimit = r.data.day_bwlimit;
        this.night_bwlimit = r.data.night_bwlimit;
        this.limit_during_day = r.data.limit_during_day;
        this.limit_during_night = r.data.limit_during_night;
      });
    },
    showNiceDate(val) {
      let newDate = date.buildDate({ hours: val });
      return date.formatDate(newDate, "h A");
    }
  },
  created() {
    this.getSettings();
  },
  beforeDestroy() {
    this.$emit("close");
  }
};
</script>