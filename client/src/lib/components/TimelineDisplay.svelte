<script lang="ts">
  import type { TimelineItem } from '../../app';
  import DateDisplay from './DateDisplay.svelte';
  
  export let item: TimelineItem & { left: boolean }

</script>


<div class="bg-white w-[150%] transform {item.left ? "-translate-x-[20%]" : "-translate-x-[15%]"}">
  <div class="grid grid-cols-1 place-items-center mt-4">
    <div class="w-fit">
      <DateDisplay date={item.createdAt} location="Australia" />
    </div>
  </div>
</div>