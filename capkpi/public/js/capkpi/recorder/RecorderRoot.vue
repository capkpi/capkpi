<template>
	<keep-alive include="RecorderDetail">
		<router-view/>
	</keep-alive>
</template>

<script>
export default {
	name: "RecorderRoot",
	watch: {
		$route() {
			capkpi.router.current_route = capkpi.router.parse();
			capkpi.breadcrumbs.update();
		}
	}
};
</script>
