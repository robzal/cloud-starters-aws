#read in the appropriate env file
. .env

cd ./src/pipeline-lambdas/
for d in * ; do 
    echo $d; 
    if [ ! -d ../../build/$d ] 
    then
        mkdir ../../build/$d;
    fi
    rm -rf ../../build/$d/*
    pip3 install -t ../../build/$d -r $d/requirements.txt
    cp $d/lambda_function.py ../../build/$d
    VERSION=$(cat $d/version.txt)
    pushd ../../build/$d
    rm ../../packages/$d-$VERSION.zip
    zip -r ../../packages/$d-$VERSION.zip *
    popd
done
