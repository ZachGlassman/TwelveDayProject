import React from 'react';
import ReactDOM from 'react-dom';

export class StockEntry extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            value: ''
        }

        this.handleChange = this
            .handleChange
            .bind(this);
        this.handleSubmit = this
            .handleSubmit
            .bind(this);
    }

    handleChange(event) {
        this.setState({value: event.target.value});
    }

    handleSubmit(event) {
        event.preventDefault();
    }
    render() {
        return (< input type = "text" value = {
            this.state.value
        }
        onChange = {
            this.handleChange
        } />)
    }
}