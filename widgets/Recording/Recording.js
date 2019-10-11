import React, { Component } from 'react';
import { PythonInterface } from 'reactopya';
import TimeseriesView from '../TimeseriesView/TimeseriesView';
import Accordion from '../jscommon/Accordion/Accordion';
const config = require('./Recording.json');

export default class Recording extends Component {
    static title = 'View a recording from a SpikeForest analysis'
    static reactopyaConfig = config
    constructor(props) {
        super(props);
        this.state = {
            // javascript state
            
            // python state
            status: '',
            status_message: ''
        }
    }
    componentDidMount() {
        this.pythonInterface = new PythonInterface(this, config);
        this.pythonInterface.start();
    }
    componentWillUnmount() {
        this.pythonInterface.stop();
    }
    render() {
        const object = this.props.object || {};
        console.log('----props', this.props, object);
        let panels = [
            {label: 'Timeseries'},
            {label: 'Test'}
        ];
        return (
            <Accordion
                panels={panels}
            >
                <TimeseriesView
                    recording={{
                        path: object.directory + '/raw.mda',
                        download_from: 'spikeforest.public',
                        samplerate: object.sampleRateHz
                    }}
                    reactopyaParent={this}
                    reactopyaChildId="timeseries"
                />
                <div>Test</div>
            </Accordion>
        );
    }
}
