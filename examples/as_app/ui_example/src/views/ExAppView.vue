<template>
	<NcContent>
		<NcAppContent>
            <div class="ui-example">
                <h1>{{ t('ui_example', 'ExApp UI example') }}</h1>
                <p>{{ t('ui_example', 'All front-end stuff kept the same for seamless migration for developers. All needed stuff is proxying via AppAPI') }}</p>
                <NcInputField :value.sync="initialState.initial_value" :label="t('ui_example', 'Initial value')" :disabled="true" />
                <p>
                    {{ t('ui_example', 'Initial value from store') }}: {{ initialStateValue }}
                </p>
                <NcButton @click="verifyInitialValue">
                    {{ t('ui_example', 'Verify initial value') }}
                </NcButton>
            </div>
		</NcAppContent>
	</NcContent>
</template>

<script>
import { loadState } from '@nextcloud/initial-state'
import NcContent from '@nextcloud/vue/dist/Components/NcContent.js'
import NcAppContent from '@nextcloud/vue/dist/Components/NcAppContent.js'
import NcInputField from '@nextcloud/vue/dist/Components/NcInputField.js'
import NcButton from '@nextcloud/vue/dist/Components/NcButton.js'

export default {
	name: 'ExAppView',
	components: {
		NcInputField,
		NcButton,
		NcContent,
		NcAppContent,
	},
	data() {
		return {
			initialState: loadState('ui_example', 'ui_example_state'),
		}
	},
	computed: {
		initialStateValue() {
			return this.$store.getters.getInitialStateValue
		},
	},
	beforeMount() {
		this.$store.commit('setInitialStateValue', this.initialState?.initial_value)
	},
	methods: {
		verifyInitialValue() {
			this.$store.dispatch('verifyInitialStateValue', this.initialState?.initial_value)
		},
	},
}
</script>

<style scoped>
.ui-example {
	width: 100%;
	max-width: 600px;
	display: flex;
	flex-direction: column;
	align-items: center;
	margin: 0 auto;
}
</style>
