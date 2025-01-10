<template>
  <bk-dialog
    v-model="isShowDialog"
    :width="width"
    :close-icon="true"
    :show-footer="false"
    :ext-cls="`iam-limit-org-dialog ${extCls}`"
    @after-leave="handleAfterLeave"
  >
    <div slot="header" class="confirm-content-wrapper">
      <Icon bk type="info-circle-shape" class="warn" />
      <div class="header-title">{{ title }}</div>
    </div>
  </bk-dialog>
</template>

<script>
  export default {
    props: {
      show: {
        type: Boolean,
        default: false
      },
      width: {
        type: Number,
        default: 400
      },
      title: {
        type: String,
        default: ''
      },
      extCls: {
        type: String,
        default: ''
      }
    },
    data () {
      return {
        isShowDialog: false
      };
    },
    watch: {
      show: {
        handler (value) {
          this.isShowDialog = !!value;
        },
        immediate: true
      }
    },
    methods: {
      handleAfterLeave () {
        this.$emit('update:show', false);
        this.$emit('on-after-leave');
      }
    }
  };
</script>

<style lang="postcss" scoped>
.iam-limit-org-dialog {
  .confirm-content-wrapper {
    display: flex;
    align-items: center;
    padding-bottom: 8px;
    word-break: break-all;
    .warn {
      font-size: 22px;
      color: #ffb848;
    }
    .header-title {
      font-size: 14px;
      padding-left: 8px;
      text-align: left;
    }
  }
}
</style>
