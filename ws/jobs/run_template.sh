ls /usr/lib/spark/bin
mkdir bin
cp /usr/lib/spark/bin/load-spark-env.sh bin
cat bin/load-spark-env.sh
mv pyspark bin/
mkdir conf
grep -v PYSPARK_PYTHON /usr/lib/spark/conf/spark-env.sh > conf/spark-env.sh
echo "export PYSPARK_PYTHON=./etk_env.zip/etk_env/bin/python" >> conf/spark-env.sh
echo "export DEFAULT_PYTHON=./etk_env.zip/etk_env/bin/python" >> conf/spark-env.sh
echo "export PYSPARK_DRIVER_PYTHON=./etk_env/etk_env/bin/python" >> conf/spark-env.sh
export PYSPARK_PYTHON=./etk_env.zip/etk_env/bin/python
export PYSPARK_DRIVER_PYTHON=./etk_env/etk_env/bin/python
export DEFAULT_PYTHON=./etk_env.zip/etk_env/bin/python
./etk_env/etk_env/bin/python -c "print 'hello jason'"
./bin/pyspark \
  --conf spark.yarn.appMasterEnv.PYSPARK_PYTHON=./etk_env.zip/etk_env/bin/python \
  --conf spark.executorEnv.PYSPARK_PYTHON=./etk_env.zip/etk_env/bin/python \
  --conf spark.executorEnv.DEFAULT_PYTHON=./etk_env.zip/etk_env/bin/python \
 --master yarn-client \
 --num-executors 200  --executor-memory 12g \
--archives etk_env.zip \
    --conf spark.eventLog.enabled=true \
    --conf spark.eventLog.dir=hdfs://memex/user/spark/applicationHistory \
    --conf spark.yarn.historyServer.address=memex-spark-master.xdata.data-tactics-corp.com:18080 \
    --conf spark.logConf=true \
 --py-files python-lib.zip \
