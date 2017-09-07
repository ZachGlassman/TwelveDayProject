import React from 'react';
import ReactDOM from 'react-dom';
import createFilterOptions from 'react-select-fast-filter-options';
import VirtualizedSelect from 'react-virtualized-select';
import 'react-select/dist/react-select.css';
import 'react-virtualized/styles.css';
import 'react-virtualized-select/styles.css';

const options = $TICK_NAMES.map((name) => {
    return {value: name, label: name}
})
const filterOptions = createFilterOptions({options})

class GetOptions extends React.Component {
    constructor(props) {
        super(props);
        this.state = {}
    }

    render() {
        return (<VirtualizedSelect
            id="ticker-select"
            name="ticker-select"
            multi={true}
            joinValues={true}
            filterOptions={filterOptions}
            options={options}
            onChange={(selectValue) => this.setState({selectValue})}
            value={this.state.selectValue}/>)
    }
}

ReactDOM.render(
    <GetOptions/>, document.getElementById('root'));