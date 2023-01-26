#read in the appropriate env file
# . .env

# cd ..
F_DIR=./src/functions
for d in $(find $F_DIR -type d -depth 1 | awk -F/ '{print $NF}'); do 
    echo $d; 
    if [ ! -d ./build ] 
    then
        mkdir ./build;
    fi
    if [ ! -d ./build/$d ] 
    then
        mkdir ./build/$d;
    fi
    if [ ! -d ./packages ] 
    then
        mkdir ./packages;
    fi
    rm -rf ./build/$d/*
    pip3 install -t ./build/$d -r $F_DIR/$d/requirements.txt
    cp $F_DIR/$d/lambda.py ./build/$d
    VERSION=$(cat $F_DIR/$d/version.txt)
    if [ -f ./packages/$d-$VERSION.zip ] 
    then
        rm ./packages/$d-$VERSION.zip;
    fi
    pushd ./build/$d
    zip -r ../../packages/$d-$VERSION.zip *
    popd
done
