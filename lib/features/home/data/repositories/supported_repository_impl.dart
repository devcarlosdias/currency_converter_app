import 'package:currency_converter_app/features/home/data/datasources/supported_datasource.dart';
import 'package:currency_converter_app/features/home/domain/entity/supported_currency.dart';
import 'package:currency_converter_app/features/home/domain/repository/supported_repository.dart';
import 'package:dartz/dartz.dart';

class SupportedRepositoryImpl implements SupportedRepository {
  final SupportedDatasource datasource;
  SupportedRepositoryImpl(this.datasource);

  @override
  Future<Either<Exception, List<SupportedCurrency>>>
  getSupportedCurrency() async {
    try {
      final result = await datasource.getSupportedCurrency();
      return Right(result);
    } catch (e) {
      return Left(Exception(e.toString()));
    }
  }
}
