from nicegui import ui


class BandwidthGraph:
    def __init__(self, max_count: int):
        self._max_count: int = 60

        byte_formatter: str = '''
        function (value) {
            power = Math.floor(Math.log(value) / Math.log(1024))

            const prefix = ['B', 'KiB', 'MiB', 'GiB', 'TiB', 'I dont think so']
            value = Math.floor(value / (power * 1024))
            if (value < 1 || !isFinite(value)) {
                return ''
            }
            return `${value} ${prefix[power] || '?'}`
        }
        '''
        self._bandwidth_chart: ui.echart = ui.echart({
            'xAxis': {
                'type': 'category',
                'show': False},
            'yAxis': {
                'type': 'value',
                'axisLabel': {
                    ':formatter': byte_formatter}},
            'legend': {
                'show': 'false'},
            'series': [
                {'type': 'line',
                 'color': '#ea7e20',
                 'areaStyle': {'color': '#ea7e20'},
                 'showSymbol': False,
                 'name': 'Bytes in',
                 'data': [0] * self._max_count},
                {'type': 'line',
                 'color': '#003366',
                 'areaStyle': {'color': '#003366'},
                 'showSymbol': False,
                 'name': 'Bytes out',
                 'data': [0] * self._max_count},
            ],
        }).classes('col-span-full')

    def update_graph(self, bytes_in: int, bytes_out: int) -> None:
        chart_in_data = self._bandwidth_chart.options['series'][0]['data']
        chart_out_data = self._bandwidth_chart.options['series'][1]['data']

        chart_in_data.append(bytes_in)
        chart_out_data.append(bytes_out)

        if len(chart_in_data) > self._max_count:
            chart_in_data.pop(0)
            chart_out_data.pop(0)
