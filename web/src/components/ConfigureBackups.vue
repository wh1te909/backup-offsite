<template>
  <q-card style="min-width: 60vw" class="q-pa-xs">
    <q-card-section>
      <div class="row items-center">
        <div class="text-h6">{{ agent.hostname }} - Backup Schedule</div>
        <q-space />
        <q-btn icon="close" flat round dense v-close-popup />
      </div>
    </q-card-section>

    <q-separator />

    <q-card-section class="q-pa-md">
      <div class="text-overline">
        Weekly Backups:
        <q-badge class="text-h6" color="blue" :label="weeklyBackups" />
      </div>
      <br />
      <q-form @submit.prevent="editSchedule" class="q-gutter-md">
        <!-- monday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="monday" @input="mondayTimes = []" />Mon
          </div>
          <div class="col">
            <q-select
              :disable="!monday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="mondayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- tuesday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="tuesday" @input="tuesdayTimes = []" />Tue
          </div>
          <div class="col">
            <q-select
              :disable="!tuesday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="tuesdayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- wednesday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="wednesday" @input="wednesdayTimes = []" />Wed
          </div>
          <div class="col">
            <q-select
              :disable="!wednesday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="wednesdayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- thursday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="thursday" @input="thursdayTimes = []" />Thur
          </div>
          <div class="col">
            <q-select
              :disable="!thursday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="thursdayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- friday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="friday" @input="fridayTimes = []" />Fri
          </div>
          <div class="col">
            <q-select
              :disable="!friday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="fridayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- saturday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="saturday" @input="saturdayTimes = []" />Sat
          </div>
          <div class="col">
            <q-select
              :disable="!saturday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="saturdayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>
        <!-- sunday -->
        <div class="row">
          <div class="col-1">
            <q-checkbox v-model="sunday" @input="sundayTimes = []" />Sun
          </div>
          <div class="col">
            <q-select
              :disable="!sunday"
              dense
              options-dense
              label="Backup times (multiple can be selected)"
              filled
              clearable
              v-model="sundayTimes"
              multiple
              :options="timeOptions"
              use-chips
              stack-label
              emit-value
              map-options
            />
          </div>
        </div>

        <div>
          <q-btn label="Save" type="submit" color="primary" />
          <q-btn label="Cancel" v-close-popup color="primary" flat class="q-ml-sm" />
        </div>
      </q-form>
    </q-card-section>
    <q-inner-loading :showing="!ready">
      <q-spinner-bars size="100px" color="primary" />
    </q-inner-loading>
  </q-card>
</template>

<script>
import mixins from "../mixins/mixins";
export default {
  name: "ConfigureBackups",
  props: ["agent"],
  mixins: [mixins],
  data() {
    return {
      ready: false,
      monday: false,
      tuesday: false,
      wednesday: false,
      thursday: false,
      friday: false,
      saturday: false,
      sunday: false,
      mondayTimes: [],
      tuesdayTimes: [],
      wednesdayTimes: [],
      thursdayTimes: [],
      fridayTimes: [],
      saturdayTimes: [],
      sundayTimes: [],
      timeOptions: [
        { label: "12 AM", value: 0 },
        { label: "1 AM", value: 1 },
        { label: "2 AM", value: 2 },
        { label: "3 AM", value: 3 },
        { label: "4 AM", value: 4 },
        { label: "5 AM", value: 5 },
        { label: "6 AM", value: 6 },
        { label: "7 AM", value: 7 },
        { label: "8 AM", value: 8 },
        { label: "9 AM", value: 9 },
        { label: "10 AM", value: 10 },
        { label: "11 AM", value: 11 },
        { label: "12 PM", value: 12 },
        { label: "1 PM", value: 13 },
        { label: "2 PM", value: 14 },
        { label: "3 PM", value: 15 },
        { label: "4 PM", value: 16 },
        { label: "5 PM", value: 17 },
        { label: "6 PM", value: 18 },
        { label: "7 PM", value: 19 },
        { label: "8 PM", value: 20 },
        { label: "9 PM", value: 21 },
        { label: "10 PM", value: 22 },
        { label: "11 PM", value: 23 }
      ]
    };
  },
  computed: {
    weeklyBackups() {
      const all = [
        ...this.mondayTimes,
        ...this.tuesdayTimes,
        ...this.wednesdayTimes,
        ...this.thursdayTimes,
        ...this.fridayTimes,
        ...this.saturdayTimes,
        ...this.sundayTimes
      ];

      return all.length;
    }
  },
  methods: {
    editSchedule() {
      this.$q.loading.show();
      const data = {
        pk: this.agent.id,
        mondayTimes: this.mondayTimes,
        tuesdayTimes: this.tuesdayTimes,
        wednesdayTimes: this.wednesdayTimes,
        thursdayTimes: this.thursdayTimes,
        fridayTimes: this.fridayTimes,
        saturdayTimes: this.saturdayTimes,
        sundayTimes: this.sundayTimes
      };
      this.$axios
        .post("/core/backupschedule/", data)
        .then(r => {
          this.$q.loading.hide();
          this.$emit("close");
          this.notifySuccess("Schedule was updated!");
        })
        .catch(() => {
          this.$q.loading.hide();
          this.notifyError("Something went wrong");
        });
    },
    getSchedule() {
      this.$axios.get(`/core/${this.agent.id}/backupschedule/`).then(r => {
        if (r.data.backup_schedule.mon.length !== 0) {
          this.monday = true;
        }
        if (r.data.backup_schedule.tue.length !== 0) {
          this.tuesday = true;
        }
        if (r.data.backup_schedule.wed.length !== 0) {
          this.wednesday = true;
        }
        if (r.data.backup_schedule.thu.length !== 0) {
          this.thursday = true;
        }
        if (r.data.backup_schedule.fri.length !== 0) {
          this.friday = true;
        }
        if (r.data.backup_schedule.sat.length !== 0) {
          this.saturday = true;
        }
        if (r.data.backup_schedule.sun.length !== 0) {
          this.sunday = true;
        }

        this.mondayTimes = r.data.backup_schedule.mon;
        this.tuesdayTimes = r.data.backup_schedule.tue;
        this.wednesdayTimes = r.data.backup_schedule.wed;
        this.thursdayTimes = r.data.backup_schedule.thu;
        this.fridayTimes = r.data.backup_schedule.fri;
        this.saturdayTimes = r.data.backup_schedule.sat;
        this.sundayTimes = r.data.backup_schedule.sun;
        this.ready = true;
      });
    }
  },
  created() {
    this.getSchedule();
  },
  beforeDestroy() {
    this.$emit("close");
  }
};
</script>