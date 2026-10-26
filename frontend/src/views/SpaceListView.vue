<script setup>
// 商业项目列表 —— 复用 WorkListView 的组件结构
// 通过 route meta 或 props 区分 page_key
</script>

<template>
  <WorkList page-key="commercial" page-title="商业项目" />
</template>

<script>
import WorkList from './WorkListView.vue'
export default { components: { WorkList } }
</script>
