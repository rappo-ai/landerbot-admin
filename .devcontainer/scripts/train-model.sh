#!/bin/bash

(cd /app/dataset && rasa train -vv > /app/train_logs.txt)
